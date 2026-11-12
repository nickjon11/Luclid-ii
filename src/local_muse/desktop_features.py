"""Luclid-ii v0.6.20 desktop utilities; local-first, explicit user actions."""
import json
import csv
import uuid
from datetime import timezone
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import requests
from PySide6.QtCore import Qt, QProcess, QTimer, QUrl, QThread, Signal, QSettings
from PySide6.QtGui import QDesktopServices, QColor, QTextCharFormat, QBrush, QPalette
from PySide6.QtWidgets import (QWidget,QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QListWidget,QLineEdit,QFileDialog,QMessageBox,QTreeWidget,QTreeWidgetItem,
    QPlainTextEdit,QComboBox,QDialogButtonBox,QTabWidget,QCheckBox,QInputDialog, QDateTimeEdit, QMenu, QAbstractItemView, QSpinBox, QFormLayout, QProgressDialog, QHeaderView, QScrollArea, QApplication, QCalendarWidget, QSplitter, QTableWidget, QTableWidgetItem, QColorDialog, QTableView)

HOME = Path.home()/'.luclid-ii'
DOCS = HOME/'saved-documents'
TASKS = HOME/'tasks.json'

def documents_dialog(parent):
    DOCS.mkdir(parents=True,exist_ok=True)
    dlg=QDialog(parent); dlg.setWindowTitle('Luclid-ii — Saved Documents'); dlg.resize(780,520)
    lay=QVBoxLayout(dlg); lay.addWidget(QLabel('Saved Documents — local library (files remain on your computer)'))
    search=QLineEdit();search.setPlaceholderText('Search saved documents…');lay.addWidget(search)
    tree=QTreeWidget();tree.setHeaderLabels(['Name','Type','Size','Modified']);lay.addWidget(tree)
    def selected():
        item=tree.currentItem()
        return Path(item.data(0,Qt.ItemDataRole.UserRole)) if item else None
    def refresh():
        tree.clear();needle=search.text().casefold()
        for path in sorted(DOCS.rglob('*'),key=lambda p:p.name.casefold()):
            if not path.is_file() or needle not in path.name.casefold():continue
            try:
                st=path.stat();item=QTreeWidgetItem(tree,[str(path.relative_to(DOCS)),path.suffix.upper() or 'FILE',f'{st.st_size/1024:.1f} KB',datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M')]);item.setData(0,Qt.ItemDataRole.UserRole,str(path))
            except OSError:pass
    search.textChanged.connect(refresh)
    actions=QHBoxLayout();lay.addLayout(actions)
    def add_file():
        paths,_=QFileDialog.getOpenFileNames(dlg,'Add documents to Luclid-ii library')
        import shutil
        for raw in paths:
            src=Path(raw);dst=DOCS/src.name
            if dst.exists():
                if QMessageBox.question(dlg,'Replace file',f'Replace {dst.name}?')!=QMessageBox.StandardButton.Yes:continue
            try:shutil.copy2(src,dst)
            except OSError as exc:QMessageBox.warning(dlg,'Copy failed',str(exc))
        refresh()
    def open_file():
        path=selected()
        if path and path.exists():QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
    def rename_file():
        path=selected()
        if not path:return
        name,ok=QInputDialog.getText(dlg,'Rename document','New filename:',text=path.name)
        if ok and name and name not in ('.','..') and Path(name).name==name:
            try:path.rename(path.with_name(name));refresh()
            except OSError as exc:QMessageBox.warning(dlg,'Rename failed',str(exc))
    def delete_file():
        path=selected()
        if path and QMessageBox.question(dlg,'Delete saved document',f'Permanently delete {path.name}?')==QMessageBox.StandardButton.Yes:
            try:path.unlink();refresh()
            except OSError as exc:QMessageBox.warning(dlg,'Delete failed',str(exc))
    for label,fn in [('Add File…',add_file),('Open',open_file),('Rename',rename_file),('Delete…',delete_file),('Open Library Folder',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(DOCS))))]:
        btn=QPushButton(label);btn.clicked.connect(fn);actions.addWidget(btn)
    refresh();dlg.exec()

def model_dialog(parent):
    dlg=QDialog(parent);dlg.setWindowTitle('Luclid-ii — AI Models (Ollama)');dlg.resize(790,470)
    lay=QVBoxLayout(dlg);lay.addWidget(QLabel('Installed models — actual disk usage from Ollama; RAM/VRAM needs depend on quantization and context length.'))
    tree=QTreeWidget();tree.setHeaderLabels(['Model','Storage','Estimated runtime memory','Status']);lay.addWidget(tree)
    def refresh():
        tree.clear()
        try:
            resp=requests.get('http://127.0.0.1:11434/api/tags',timeout=5);resp.raise_for_status()
            models=resp.json().get('models',[])
            for m in models:
                name=m.get('name','');size=m.get('size',0)
                gb=size/(1024**3)
                item=QTreeWidgetItem(tree,[name,f'{gb:.2f} GB',f'~{gb*1.2:.1f}–{gb*2:.1f} GB (rough estimate)','Installed'])
                item.setData(0,Qt.ItemDataRole.UserRole,name)
            lay.itemAt(0).widget().setText(f'Installed models: {len(models)} — {sum(m.get("size",0) for m in models)/(1024**3):.2f} GB reported (shared layers may overlap).')
        except (requests.RequestException,ValueError) as exc:QMessageBox.warning(dlg,'Ollama unavailable',str(exc))
    buttons=QHBoxLayout();lay.addLayout(buttons)
    def remove():
        item=tree.currentItem()
        if not item:return
        name=item.data(0,Qt.ItemDataRole.UserRole)
        if name==parent.model.currentText():
            if QMessageBox.warning(dlg,'Active model',f'{name} is currently selected. Uninstalling it will prevent further use until reinstalled. Continue?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        if QMessageBox.question(dlg,'Confirm uninstall',f'Remove {name} from Ollama?\nThis removes its local model data and cannot be undone.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        try:
            resp=requests.delete('http://127.0.0.1:11434/api/delete',json={'model':name},timeout=60);resp.raise_for_status();refresh();parent.refresh_models()
        except requests.RequestException as exc:QMessageBox.warning(dlg,'Uninstall failed',str(exc))
    for label,fn in [('Refresh',refresh),('Download Other Models…',parent.download_other_models),('Uninstall Selected…',remove)]:
        btn=QPushButton(label);btn.clicked.connect(fn);buttons.addWidget(btn)
    refresh();dlg.exec()

class TaskEditor(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        task=task or {}
        self.setWindowTitle('Luclid-ii — Edit Task')
        self.resize(450,250)
        form=QFormLayout(self)
        self.name=QLineEdit(task.get('name',''));form.addRow('Task:',self.name)
        self.due=QDateTimeEdit(self);self.due.setCalendarPopup(True)
        self.due.setDisplayFormat('yyyy-MM-dd HH:mm')
        try:self.due.setDateTime(datetime.strptime(task['due'],'%Y-%m-%d %H:%M'))
        except (KeyError,ValueError):self.due.setDateTime(datetime.now()+timedelta(hours=1))
        form.addRow('Due (local time):',self.due)
        self.has_due=QCheckBox('Enable due-time reminder');self.has_due.setChecked(bool(task.get('due',True)))
        form.addRow('',self.has_due)
        self.duration=QSpinBox();self.duration.setRange(0,720);self.duration.setSuffix(' min');self.duration.setValue(int(task.get('duration_minutes',60)));form.addRow('Estimated duration:',self.duration)
        self.status=QComboBox();self.status.addItems(['Pending','In Progress','Completed','Cancelled'])
        self.status.setCurrentText(task.get('status','Completed' if task.get('done') else 'Pending'))
        form.addRow('Status:',self.status)
        self.importance=QComboBox()
        self.importance.addItems(['Critical','High','Medium','Low','Custom'])
        self.importance.setCurrentText(task.get('importance','Medium'))
        form.addRow('Importance:',self.importance)
        self.custom_color=task.get('importance_color','#a777e5')
        choose_color=QPushButton('Choose custom color…')
        choose_color.clicked.connect(self.pick_color)
        form.addRow('',choose_color)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);form.addRow(buttons)
    def pick_color(self):
        color=QColorDialog.getColor(QColor(self.custom_color),self,'Choose task marker color')
        if color.isValid():
            self.custom_color=color.name()
            self.importance.setCurrentText('Custom')

    def result_task(self, original=None):
        t=dict(original or {})
        due=self.due.dateTime().toString('yyyy-MM-dd HH:mm') if self.has_due.isChecked() else ''
        if t.get('due')!=due:t['notified']=False
        t.update(name=self.name.text().strip(),due=due,duration_minutes=self.duration.value(),status=self.status.currentText(),done=self.status.currentText()=='Completed',importance=self.importance.currentText(),importance_color=self.custom_color)
        return t

def schedule_subtasks(tasks, today, deadline, hours_per_day, mode):
    """Assign dates in Python using local time; never trust model-generated dates."""
    start = today.date()
    end = deadline.date()
    if end < start:
        raise ValueError('The deadline is in the past. Choose a future deadline.')
    days = (end - start).days + 1
    capacity = max(15, int(hours_per_day) * 60)
    total = sum(item['duration'] for item in tasks)
    if total > days * capacity:
        raise ValueError(f'This plan needs {total} minutes but only {days * capacity} minutes are available before the deadline. Increase hours/day or extend the deadline.')
    # Relaxed uses more of the available time; intensive starts immediately.
    if mode == 'Relaxed' and days > 1:
        slots = min(days, max((total + capacity - 1) // capacity, int(days * .8)))
    elif mode == 'Balanced' and days > 1:
        slots = min(days, max((total + capacity - 1) // capacity, int(days * .6)))
    else:
        slots = min(days, max(1, (total + capacity - 1) // capacity))
    positions = [round(i * (days - 1) / max(1, slots - 1)) for i in range(slots)] if slots > 1 else [0]
    remaining = [capacity] * len(positions)
    cursor = 0
    base_hour = 9 if mode == 'Intensive' else (18 if mode == 'Balanced' else 14)
    for item in tasks:
        duration = item['duration']
        # A subtask can span several work sessions; record its starting date.
        if duration > capacity:
            raise ValueError(f"'{item['name']}' needs more than {hours_per_day} hours in one day. Break it into smaller subtasks.")
        while cursor < len(positions) and remaining[cursor] < duration:
            cursor += 1
        if cursor >= len(positions):
            raise ValueError('Unable to fit the proposed tasks into the available daily schedule.')
        scheduled_day = start + timedelta(days=positions[cursor])
        start_minutes = base_hour * 60 + (capacity - remaining[cursor])
        if scheduled_day == today.date():
            start_minutes = max(start_minutes, ((today.hour * 60 + today.minute + 14)//15)*15)
        if scheduled_day == deadline.date() and start_minutes + duration > deadline.hour*60+deadline.minute:
            raise ValueError('The proposed schedule exceeds the deadline time. Increase available hours or extend the deadline.')
        if start_minutes + duration > 24*60:
            raise ValueError('Task would run past midnight. Reduce daily hours or split the task.')
        item['date'] = scheduled_day.strftime('%Y-%m-%d')
        item['time'] = f'{start_minutes//60:02d}:{start_minutes%60:02d}'
        remaining[cursor] -= duration
    return tasks


class PlanWorker(QThread):
    complete=Signal(object,str)
    def __init__(self,model,goal,deadline,hours,mode):
        super().__init__();self.model=model;self.goal=goal;self.deadline=deadline;self.hours=hours;self.mode=mode
    def run(self):
        import re
        now = datetime.now()
        try:
            end = datetime.strptime(self.deadline, '%Y-%m-%d %H:%M')
            if end <= now:
                raise ValueError('Deadline must be later than the current local time.')
            schema={'type':'object','properties':{'tasks':{'type':'array','items':{'type':'object','properties':{'name':{'type':'string'},'duration_minutes':{'type':'integer'}},'required':['name','duration_minutes']}}},'required':['tasks']}
            prompt=(f'Current LOCAL date and time: {now:%Y-%m-%d %H:%M}. Deadline: {self.deadline}. '
                    f'Break the following goal into 3 to 12 manageable, sequential subtasks: {self.goal}. '
                    f'Available hours per day: {self.hours}; pace: {self.mode}. '
                    'Return only a JSON object with a tasks array. Each task needs a concise name and realistic integer duration_minutes. '
                    'Do NOT assign dates: the application schedules the tasks itself.')
            error = None
            for attempt in range(2):
                try:
                    messages=[{'role':'user','content':prompt}]
                    if attempt:
                        messages.append({'role':'user','content':'Your last response could not be parsed. Output ONLY valid JSON matching the required schema. No Markdown, no explanation.'})
                    r=requests.post('http://127.0.0.1:11434/api/chat',json={
                        'model':self.model,'stream':False,'format':schema,'messages':messages,
                        'options':{'temperature':0,'num_predict':2400}},timeout=240)
                    r.raise_for_status()
                    message=r.json().get('message',{})
                    content=message.get('content','').strip()
                    if not content:raise ValueError('Model returned an empty response')
                    try:obj=json.loads(content)
                    except json.JSONDecodeError:
                        match=re.search(r'\{.*\}',content,re.S)
                        if not match:raise ValueError('Model did not return valid JSON')
                        obj=json.loads(match.group(0))
                    if not isinstance(obj,dict) or not isinstance(obj.get('tasks'),list) or not obj['tasks']:
                        raise ValueError('Model did not return a valid tasks array')
                    valid=[]
                    for item in obj['tasks'][:15]:
                        if not isinstance(item,dict):continue
                        name=str(item.get('name','')).strip()[:180]
                        try:duration=max(15,min(720,int(item.get('duration_minutes',60))))
                        except (ValueError,TypeError):duration=60
                        if name:valid.append({'name':name,'duration':duration})
                    if not valid:raise ValueError('No valid subtasks were generated')
                    valid=schedule_subtasks(valid,now,end,self.hours,self.mode)
                    self.complete.emit(valid,'')
                    return
                except (ValueError,KeyError,TypeError) as exc:
                    error=exc
                    if attempt:break
            raise ValueError(str(error))
        except Exception as exc:self.complete.emit([],str(exc))

class PlannerDialog(QDialog):
    def __init__(self,task_page):
        super().__init__(task_page);self.page=task_page
        self.setWindowTitle('Luclid-ii — AI Task Planner');self.resize(800,590);self.setMinimumSize(540,400)
        lay=QVBoxLayout(self)
        intro=QLabel('Describe a goal. Your local Ollama model will draft a schedule; nothing is saved until you approve individual tasks.');intro.setWordWrap(True);lay.addWidget(intro)
        self.goal=QPlainTextEdit();self.goal.setPlaceholderText('Example: Finish my cybersecurity presentation by December 5');self.goal.setMaximumHeight(75);lay.addWidget(self.goal)
        settings=QHBoxLayout();lay.addLayout(settings)
        self.deadline=QDateTimeEdit();self.deadline.setCalendarPopup(True);self.deadline.setDisplayFormat('yyyy-MM-dd HH:mm');self.deadline.setDateTime(datetime.now()+timedelta(days=14))
        settings.addWidget(QLabel('Deadline:'));settings.addWidget(self.deadline,1)
        self.hours=QSpinBox();self.hours.setRange(1,12);self.hours.setValue(2);settings.addWidget(QLabel('Hours/day:'));settings.addWidget(self.hours)
        self.pace=QComboBox();self.pace.addItems(['Relaxed','Balanced','Intensive']);self.pace.setCurrentText('Balanced');settings.addWidget(self.pace)
        model_row=QHBoxLayout();lay.addLayout(model_row)
        model_row.addWidget(QLabel('AI model:'))
        self.model_choice=QComboBox();self.model_choice.setMinimumWidth(160);model_row.addWidget(self.model_choice,1)
        refresh_btn=QPushButton('Refresh Models');refresh_btn.clicked.connect(self.refresh_model_choices);model_row.addWidget(refresh_btn)
        self.refresh_model_choices()
        self.generate=QPushButton('Generate Draft Plan');self.generate.clicked.connect(self.generate_plan);lay.addWidget(self.generate)
        self.message=QLabel('Review the selected model, goal, and deadline before generating a draft.');self.message.setWordWrap(True);lay.addWidget(self.message)
        self.table=QTreeWidget();self.table.setHeaderLabels(['Approve','Subtask','Date','Start','Est. minutes']);self.table.setRootIsDecorated(False);self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection);lay.addWidget(self.table)
        controls=QHBoxLayout();lay.addLayout(controls)
        for label,callback in [('Edit Selected…',self.edit_selected),('Remove Selected',self.remove_selected),('Approve Selected Tasks',self.approve)]:
            btn=QPushButton(label);btn.clicked.connect(callback);controls.addWidget(btn)
        self.worker=None
    def active_main_model(self):
        # The Tasks page is an embedded child, not the main application window.
        widget=self.page
        while widget is not None:
            selector=getattr(widget,'model',None)
            if isinstance(selector,QComboBox):
                return selector.currentText().strip()
            widget=widget.parentWidget() if hasattr(widget,'parentWidget') else None
        return ''
    def refresh_model_choices(self):
        selected=self.model_choice.currentText() if self.model_choice.count() else ''
        active=self.active_main_model()
        self.model_choice.clear()
        try:
            response=requests.get('http://127.0.0.1:11434/api/tags',timeout=4)
            response.raise_for_status()
            models=[m.get('name','') for m in response.json().get('models',[]) if m.get('name')]
            self.model_choice.addItems(models)
            wanted=active if active in models else selected
            if wanted in models:self.model_choice.setCurrentText(wanted)
        except (requests.RequestException,ValueError) as exc:
            if active:self.model_choice.addItem(active)
            self.model_choice.setToolTip('Ollama could not be queried: '+str(exc))
    def generate_plan(self):
        goal=self.goal.toPlainText().strip()
        if not goal:QMessageBox.warning(self,'Missing goal','Describe what you want to accomplish.');return
        model=self.model_choice.currentText().strip()
        if not model:QMessageBox.warning(self,'Missing model','No model detected. Check Ollama and click Refresh Models.');return
        if self.deadline.dateTime().toPython() <= datetime.now():
            QMessageBox.warning(self,'Invalid deadline','Choose a deadline after the current local date and time.');return
        self.generate.setEnabled(False);self.message.setText('Generating a draft plan locally…');self.table.clear()
        self.worker=PlanWorker(model,goal,self.deadline.dateTime().toString('yyyy-MM-dd HH:mm'),self.hours.value(),self.pace.currentText())
        self.worker.complete.connect(self.generated);self.worker.start()
    def closeEvent(self,event):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self,'Generating plan','Please wait for the local AI model to finish before closing this window.')
            event.ignore()
            return
        super().closeEvent(event)
    def reject(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self,'Generating plan','Please wait for the local AI model to finish before closing this window.')
            return
        super().reject()
    def generated(self,tasks,error):
        self.generate.setEnabled(True)
        if error:self.message.setText('Could not generate plan: '+error);return
        for t in tasks:
            row=QTreeWidgetItem(self.table,['',t['name'],t['date'],t['time'],str(t['duration'])]);row.setFlags(row.flags()|Qt.ItemFlag.ItemIsUserCheckable|Qt.ItemFlag.ItemIsEditable);row.setCheckState(0,Qt.CheckState.Checked)
        self.message.setText(f'{len(tasks)} draft subtasks generated. Edit dates and names, uncheck anything you do not want, then approve.')
        self.table.resizeColumnToContents(0);self.table.resizeColumnToContents(2)
    def edit_selected(self):
        item=self.table.currentItem()
        if not item:return
        name,ok=QInputDialog.getText(self,'Edit subtask','Subtask:',text=item.text(1))
        if ok and name.strip():item.setText(1,name.strip())
        date,ok=QInputDialog.getText(self,'Schedule subtask','Date YYYY-MM-DD:',text=item.text(2))
        if ok:
            try:datetime.strptime(date,'%Y-%m-%d');item.setText(2,date)
            except ValueError:QMessageBox.warning(self,'Invalid date','Use YYYY-MM-DD.')
        start,ok=QInputDialog.getText(self,'Start time','Local time (HH:MM):',text=item.text(3))
        if ok:
            try:datetime.strptime(start,'%H:%M');item.setText(3,start)
            except ValueError:QMessageBox.warning(self,'Invalid time','Use HH:MM.')
        minutes,ok=QInputDialog.getInt(self,'Estimated time','Minutes:',int(item.text(4)),15,720,15)
        if ok:item.setText(4,str(minutes))
    def remove_selected(self):
        item=self.table.currentItem()
        if item:self.table.takeTopLevelItem(self.table.indexOfTopLevelItem(item))
    def approve(self):
        selected=[self.table.topLevelItem(i) for i in range(self.table.topLevelItemCount()) if self.table.topLevelItem(i).checkState(0)==Qt.CheckState.Checked]
        if not selected:QMessageBox.information(self,'No tasks selected','Select at least one subtask.');return
        if QMessageBox.question(self,'Approve tasks',f'Add {len(selected)} selected subtasks to Automation & Tasks?')!=QMessageBox.StandardButton.Yes:return
        for row in selected:
            try:
                date=datetime.strptime(row.text(2),'%Y-%m-%d').strftime('%Y-%m-%d')
                duration=int(row.text(4))
                start=datetime.strptime(row.text(2)+' '+row.text(3),'%Y-%m-%d %H:%M')
            except (ValueError,TypeError):QMessageBox.warning(self,'Invalid task','Correct the date and duration before approving.');return
            if start < datetime.now() or start > self.deadline.dateTime().toPython():
                QMessageBox.warning(self,'Invalid date','Approved tasks must fall between today and the selected deadline.');return
            if not row.text(1).strip():QMessageBox.warning(self,'Invalid task','A task name cannot be empty.');return
        for row in selected:
            self.page.tasks.append({'name':row.text(1).strip(),'due':row.text(2)+' '+row.text(3),'duration_minutes':int(row.text(4)),'status':'Pending','done':False,'notified':False,'source':'AI Planner'})
        self.page.save();self.page.refresh();self.accept()

class EventCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_counts={}
    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)
        count=self.event_counts.get(date,0)
        if count:
            painter.save()
            painter.setPen(QColor('#f4c76d'))
            font=painter.font();font.setPointSize(8);font.setBold(True);painter.setFont(font)
            painter.drawText(rect.adjusted(0,0,-3,-2),Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignBottom,str(count))
            painter.restore()

class TasksPage(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);HOME.mkdir(parents=True,exist_ok=True)
        layout=QVBoxLayout(self);layout.addWidget(QLabel('Automation & Tasks — local reminders, editable tasks, and AI planning'))
        layout.addWidget(QLabel('Reminders are checked while Luclid-ii is running. Right-click a task to edit its name, due date, or status.'))
        split=QSplitter(Qt.Orientation.Horizontal);layout.addWidget(split,1)
        self.setObjectName('WallpaperSurface')
        self.list=QTreeWidget();self.list.setHeaderLabels(['Task','Due (local time)','Status']);split.addWidget(self.list)
        for tree in (self.list,):
            tree.setObjectName('WallpaperSurface')
            tree.setAutoFillBackground(False)
            tree.viewport().setAutoFillBackground(False)
        side=QWidget();side.setObjectName('WallpaperSurface');side.setAutoFillBackground(False);side_layout=QVBoxLayout(side);side_layout.setContentsMargins(4,0,0,0)
        self.calendar=EventCalendar();self.calendar.setGridVisible(True)
        self.calendar.setObjectName('TransparentTaskCalendar')
        self.calendar.setAutoFillBackground(False)
        self.calendar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        self.calendar.setStyleSheet('''
            QCalendarWidget#TransparentTaskCalendar { background: transparent; }
            QCalendarWidget#TransparentTaskCalendar QWidget#qt_calendar_calendarview { background: transparent; }
            QCalendarWidget#TransparentTaskCalendar QTableView { background: transparent; border: none; }
            QCalendarWidget#TransparentTaskCalendar QTableView::item { background: transparent; }
            QCalendarWidget#TransparentTaskCalendar QAbstractItemView { background: transparent; }
        ''')
        for calendar_view in self.calendar.findChildren(QTableView):
            calendar_view.setAutoFillBackground(False)
            calendar_view.viewport().setAutoFillBackground(False)
            calendar_view.viewport().setStyleSheet('background: transparent;')
        self.calendar.setMinimumWidth(280)
        # The calendar uses a private QTableView viewport, which otherwise paints
        # the palette's opaque Base color over the wallpaper.
        for calendar_view in self.calendar.findChildren(QTableView):
            calendar_view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            calendar_view.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            palette = calendar_view.palette()
            palette.setBrush(QPalette.ColorRole.Base, QBrush(Qt.GlobalColor.transparent))
            palette.setBrush(QPalette.ColorRole.AlternateBase, QBrush(Qt.GlobalColor.transparent))
            calendar_view.setPalette(palette)
            calendar_view.viewport().setPalette(palette)

        side_layout.addWidget(self.calendar)
        self.agenda_label=QLabel('Daily schedule');side_layout.addWidget(self.agenda_label)
        self.agenda=QTreeWidget();self.agenda.setHeaderLabels(['Time','Task','Status']);self.agenda.setRootIsDecorated(False);side_layout.addWidget(self.agenda,1)
        self.agenda.setObjectName('WallpaperSurface');self.agenda.setAutoFillBackground(False);self.agenda.viewport().setAutoFillBackground(False)
        for tree in (self.list,self.agenda):
            tree.setStyleSheet('QTreeWidget#WallpaperSurface { background: transparent; } QTreeWidget#WallpaperSurface::item { background: transparent; }')
            tree.viewport().setStyleSheet('background: transparent;')
            tree.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            palette = tree.palette()
            palette.setBrush(QPalette.ColorRole.Base, QBrush(Qt.GlobalColor.transparent))
            palette.setBrush(QPalette.ColorRole.AlternateBase, QBrush(Qt.GlobalColor.transparent))
            tree.setPalette(palette)
            tree.viewport().setPalette(palette)
        self.agenda.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu);self.agenda.customContextMenuRequested.connect(self.agenda_context_menu)
        # Colors are chosen per task in Edit Task; no fixed legend.
        syncrow=QHBoxLayout();side_layout.addLayout(syncrow)
        export=QPushButton('Export Calendar…');export.clicked.connect(self.export_calendar);syncrow.addWidget(export)
        sync=QPushButton('Sync to Google…');sync.clicked.connect(self.sync_google);syncrow.addWidget(sync)
        split.addWidget(side);split.setSizes([500,500]);split.setChildrenCollapsible(False)
        self.list.setMinimumWidth(240)
        side.setMinimumWidth(280)
        self.calendar.selectionChanged.connect(self.refresh_agenda)
        self.agenda.itemDoubleClicked.connect(self.open_agenda_task)
        self.list.itemSelectionChanged.connect(self.select_task_day)
        self.list.setRootIsDecorated(False)
        self.list.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.list.header().setStretchLastSection(False)
        preferences=QSettings('Luclid-ii','Luclid-ii')
        widths=preferences.value('tasks/column_widths',[205,165,115])
        try:widths=[int(w) for w in widths]
        except (ValueError,TypeError):widths=[205,165,115]
        for index,width in enumerate(widths[:3]):self.list.setColumnWidth(index,max(65,width))
        self.list.header().sectionResized.connect(self.save_column_widths)
        self.list.setStyleSheet('QTreeWidget#WallpaperSurface { background: transparent; } QTreeWidget#WallpaperSurface::item { background: transparent; padding-top: 1px; padding-bottom: 1px; }')
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu);self.list.customContextMenuRequested.connect(self.context_menu)
        self.list.itemDoubleClicked.connect(lambda item,col:self.edit_task())
        self.tasks=[]
        try:self.tasks=json.loads(TASKS.read_text(encoding='utf-8'))
        except (OSError,ValueError):pass
        row=QHBoxLayout();layout.addLayout(row)
        for label,callback in [('New Task…',self.add_task),('AI Plan from Goal…',self.ai_plan),('Mark Done',self.done),('Delete…',self.delete_task)]:
            b=QPushButton(label);b.clicked.connect(callback);row.addWidget(b)
        self.refresh();self.timer=QTimer(self);self.timer.timeout.connect(self.check_due);self.timer.start(15000)
        QTimer.singleShot(1500,self.check_due)
    def save_column_widths(self,*args):
        QSettings('Luclid-ii','Luclid-ii').setValue('tasks/column_widths',[self.list.columnWidth(i) for i in range(3)])
    def save(self):TASKS.write_text(json.dumps(self.tasks,indent=2),encoding='utf-8')
    def refresh(self):
        self.list.clear()
        for i,task in enumerate(self.tasks):
            status=task.get('status','Completed' if task.get('done') else 'Pending')
            item=QTreeWidgetItem(self.list,['●  '+task.get('name',''),task.get('due',''),status]);item.setData(0,Qt.ItemDataRole.UserRole,i)
            item.setForeground(0,QBrush(QColor(self.marker_color(task))))
        self.refresh_calendar_markers()
        self.refresh_agenda()
    @staticmethod
    def marker_color(task):
        colors={'Critical':'#e54b5b','High':'#f59e42','Medium':'#e6c44a','Low':'#4bbe83'}
        return task.get('importance_color','#a777e5') if task.get('importance')=='Custom' else colors.get(task.get('importance','Medium'),'#e6c44a')

    def refresh_calendar_markers(self):
        from PySide6.QtCore import QDate
        # Reset formats from previous refresh, then mark dates with scheduled tasks.
        for date in getattr(self,'_marked_dates',[]):
            self.calendar.setDateTextFormat(date,QTextCharFormat())
        self._marked_dates=[]
        dates={}
        for task in self.tasks:
            raw=task.get('due','')[:10]
            date=QDate.fromString(raw,'yyyy-MM-dd')
            if date.isValid():dates.setdefault(date,[]).append(task)
        self.calendar.event_counts={date:len(items) for date,items in dates.items()}
        for date,tasks in dates.items():
            fmt=QTextCharFormat()
            # A colored date marker plus tooltip represents tasks without overwriting calendar navigation.
            color=self.marker_color(tasks[0])
            fmt.setForeground(QBrush(QColor(color)))
            fmt.setFontWeight(700)
            fmt.setFontPointSize(9 if len(tasks)>1 else 10)
            fmt.setToolTip(f'{len(tasks)} event(s)\n'+'\n'.join(f"● {t.get('name','Task')} ({t.get('due','')[-5:]})" for t in tasks))
            self.calendar.setDateTextFormat(date,fmt)
            self._marked_dates.append(date)
        self.calendar.updateCells()

    def select_task_day(self):
        i=self.index()
        if i is not None:
            try:self.calendar.setSelectedDate(datetime.strptime(self.tasks[i]['due'],'%Y-%m-%d %H:%M').date())
            except (ValueError,KeyError):pass
    def refresh_agenda(self):
        self.agenda.clear()
        selected=self.calendar.selectedDate().toString('yyyy-MM-dd')
        self.agenda_label.setText('Schedule for '+selected)
        for i,t in sorted(enumerate(self.tasks),key=lambda pair:pair[1].get('due','')):
            if not t.get('due','').startswith(selected):continue
            try:
                start=datetime.strptime(t['due'],'%Y-%m-%d %H:%M')
                end=start+timedelta(minutes=int(t.get('duration_minutes',0)))
                time_label=start.strftime('%H:%M')+'–'+end.strftime('%H:%M') if t.get('duration_minutes') else start.strftime('%H:%M')
            except (ValueError,TypeError):time_label='—'
            item=QTreeWidgetItem(self.agenda,[time_label,'●  '+t.get('name',''),t.get('status','Pending')]);item.setData(0,Qt.ItemDataRole.UserRole,i)
            item.setForeground(1,QBrush(QColor(self.marker_color(t))))
    def agenda_context_menu(self,position):
        item=self.agenda.itemAt(position)
        if item is None:return
        i=item.data(0,Qt.ItemDataRole.UserRole)
        if not isinstance(i,int):return
        for j in range(self.list.topLevelItemCount()):
            row=self.list.topLevelItem(j)
            if row.data(0,Qt.ItemDataRole.UserRole)==i:
                self.list.setCurrentItem(row)
                menu=QMenu(self)
                menu.addAction('Edit task, importance and custom color…',self.edit_task)
                menu.addAction('Mark complete',self.done)
                menu.exec(self.agenda.viewport().mapToGlobal(position))
                break
    def open_agenda_task(self,item,column):
        i=item.data(0,Qt.ItemDataRole.UserRole)
        if isinstance(i,int):
            for j in range(self.list.topLevelItemCount()):
                row=self.list.topLevelItem(j)
                if row.data(0,Qt.ItemDataRole.UserRole)==i:self.list.setCurrentItem(row);self.edit_task();break
    def export_calendar(self):
        path,selected=QFileDialog.getSaveFileName(self,'Export Luclid-ii calendar','Luclid-ii-calendar.ics','iCalendar (*.ics);;CSV (*.csv);;JSON (*.json)')
        if not path:return
        suffix=Path(path).suffix.lower()
        if not suffix:suffix='.ics';path+=suffix
        try:
            if suffix=='.json':Path(path).write_text(json.dumps(self.tasks,indent=2),encoding='utf-8')
            elif suffix=='.csv':
                with open(path,'w',newline='',encoding='utf-8-sig') as f:
                    writer=csv.writer(f);writer.writerow(['Task','Start (local)','Duration minutes','Status'])
                    for t in self.tasks:writer.writerow([t.get('name',''),t.get('due',''),t.get('duration_minutes',0),t.get('status','Pending')])
            elif suffix=='.ics':
                def esc(value):return str(value).replace('\\','\\\\').replace('\n','\\n').replace(',','\\,').replace(';','\\;')
                lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Luclid-ii//Task Calendar//EN','CALSCALE:GREGORIAN']
                for t in self.tasks:
                    if not t.get('due'):continue
                    try:start=datetime.strptime(t['due'],'%Y-%m-%d %H:%M')
                    except ValueError:continue
                    end=start+timedelta(minutes=max(1,int(t.get('duration_minutes',30))))
                    uid=t.setdefault('uid',str(uuid.uuid4()))
                    lines.extend(['BEGIN:VEVENT','UID:'+uid+'@luclid-ii','DTSTAMP:'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),'DTSTART:'+start.strftime('%Y%m%dT%H%M%S'),'DTEND:'+end.strftime('%Y%m%dT%H%M%S'),'SUMMARY:'+esc(t.get('name','Task')),'DESCRIPTION:'+esc('Luclid-ii status: '+t.get('status','Pending')),'END:VEVENT'])
                lines.append('END:VCALENDAR');Path(path).write_text('\r\n'.join(lines)+'\r\n',encoding='utf-8');self.save()
            else:raise ValueError('Unsupported file format')
            QMessageBox.information(self,'Calendar exported','Saved to '+path)
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'Export failed',str(exc))
    def sync_google(self):
        from .google_account import GoogleAccount
        account=GoogleAccount()
        if not account.connected():
            QMessageBox.information(self,'Google not connected','Connect your Google account with Calendar write permission in the Google tab first.');return
        candidates=[t for t in self.tasks if t.get('due') and not t.get('google_event_id') and t.get('status')!='Cancelled']
        if not candidates:QMessageBox.information(self,'Google sync','No new unsynchronized tasks. Existing Google events are not changed automatically.');return
        if QMessageBox.question(self,'Confirm Google Calendar sync',f'Create {len(candidates)} events in your primary Google Calendar?\nOnly new tasks are uploaded; existing events will not be overwritten.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        successes=0
        for t in candidates:
            try:
                start=datetime.strptime(t['due'],'%Y-%m-%d %H:%M').astimezone()
                end=start+timedelta(minutes=max(1,int(t.get('duration_minutes',30))))
                result=account.create_event(t.get('name','Task'),start.isoformat(),end.isoformat(),description='Luclid-ii task — '+t.get('status','Pending'))
                if result.get('id'):t['google_event_id']=result['id'];self.save();successes+=1
            except Exception as exc:
                QMessageBox.warning(self,'Google sync interrupted',f'Synced {successes} event(s). Remaining tasks were not synchronized.\n{exc}');return
        QMessageBox.information(self,'Google sync',f'Created {successes} Google Calendar event(s).')
    def index(self):
        item=self.list.currentItem();return item.data(0,Qt.ItemDataRole.UserRole) if item else None
    def add_task(self):
        dlg=TaskEditor(self)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            t=dlg.result_task()
            if not t['name']:QMessageBox.warning(self,'Missing name','Enter a task name.');return
            t.setdefault('notified',False);self.tasks.append(t);self.save();self.refresh()
    def edit_task(self):
        i=self.index()
        if i is None:return
        dlg=TaskEditor(self,self.tasks[i])
        if dlg.exec()==QDialog.DialogCode.Accepted:
            t=dlg.result_task(self.tasks[i])
            if not t['name']:QMessageBox.warning(self,'Missing name','Enter a task name.');return
            self.tasks[i]=t;self.save();self.refresh()
    def context_menu(self,position):
        item=self.list.itemAt(position)
        if item is None:return
        self.list.setCurrentItem(item)
        menu=QMenu(self)
        menu.addAction('Edit Task / Due Date / Status…',self.edit_task)
        menu.addAction('Mark Complete',self.done)
        menu.addAction('Snooze 10 Minutes',lambda:self.snooze(10))
        menu.addSeparator();menu.addAction('Delete Task…',self.delete_task)
        menu.exec(self.list.viewport().mapToGlobal(position))
    def snooze(self,minutes):
        i=self.index()
        if i is None:return
        self.tasks[i]['due']=(datetime.now()+timedelta(minutes=minutes)).strftime('%Y-%m-%d %H:%M')
        self.tasks[i]['notified']=False;self.tasks[i]['done']=False;self.tasks[i]['status']='Pending'
        self.save();self.refresh()
    def done(self):
        i=self.index()
        if i is not None:self.tasks[i]['done']=True;self.tasks[i]['status']='Completed';self.save();self.refresh()
    def delete_task(self):
        i=self.index()
        if i is not None and QMessageBox.question(self,'Delete task','Delete selected task?')==QMessageBox.StandardButton.Yes:
            self.tasks.pop(i);self.save();self.refresh()
    def ai_plan(self):
        dlg=PlannerDialog(self);dlg.exec()
    def check_due(self):
        now=datetime.now()
        for i,task in enumerate(self.tasks):
            if task.get('done') or task.get('status') in ('Completed','Cancelled') or task.get('notified') or not task.get('due'):continue
            try:due=datetime.strptime(task['due'],'%Y-%m-%d %H:%M')
            except ValueError:continue
            if now>=due:
                task['notified']=True;self.save()
                dialog=QMessageBox(self);dialog.setWindowTitle('Luclid-ii — Task Reminder')
                dialog.setText(f"Scheduled time reached: {task.get('name','Task')}\nDue: {task['due']}")
                done=dialog.addButton('Mark Complete',QMessageBox.ButtonRole.AcceptRole)
                snooze=dialog.addButton('Snooze 10 min',QMessageBox.ButtonRole.ActionRole)
                dialog.addButton('Dismiss',QMessageBox.ButtonRole.RejectRole)
                dialog.exec()
                if dialog.clickedButton()==done:task['done']=True;task['status']='Completed'
                elif dialog.clickedButton()==snooze:
                    task['due']=(datetime.now()+timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M');task['notified']=False
                self.save();self.refresh()
class TerminalPage(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);lay=QVBoxLayout(self)
        lay.addWidget(QLabel('Terminal — commands run only after you click Run and approve them.'))
        self.output=QPlainTextEdit();self.output.setObjectName('WallpaperSurface');self.output.setReadOnly(True);self.output.setAutoFillBackground(False);self.output.viewport().setAutoFillBackground(False);lay.addWidget(self.output)
        row=QHBoxLayout();lay.addLayout(row)
        self.command=QLineEdit();self.command.setPlaceholderText('Enter a command…');row.addWidget(self.command)
        self.command.returnPressed.connect(self.run)
        run=QPushButton('Run…');run.clicked.connect(self.run);row.addWidget(run)
        self.run_button=run;self.proc=None
        self.command_history=[];self.history_index=0
        self.command.installEventFilter(self)
        stop=QPushButton('Stop');stop.clicked.connect(self.stop);row.addWidget(stop)
        self.output.appendPlainText('Shell: '+('PowerShell' if sys.platform=='win32' else '/bin/sh'))
        self.workspace=None
        self.cwd=Path.home()
        self.output.appendPlainText('Directory: '+str(self.cwd))
    def set_workspace(self, folder):
        self.workspace=folder
        self.cwd=Path(folder).resolve() if folder and Path(folder).is_dir() else Path.home()
        self.output.appendPlainText('Workspace directory: '+str(self.cwd))
    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeySequence
        if obj is self.command and event.type()==QEvent.Type.KeyPress:
            if event.key()==Qt.Key.Key_Up and self.command_history:
                self.history_index=max(0,self.history_index-1)
                self.command.setText(self.command_history[self.history_index]);return True
            if event.key()==Qt.Key.Key_Down and self.command_history:
                self.history_index=min(len(self.command_history),self.history_index+1)
                self.command.setText(self.command_history[self.history_index] if self.history_index<len(self.command_history) else '');return True
            if event.key()==Qt.Key.Key_Escape:
                self.command.clear();return True
            if event.matches(QKeySequence.StandardKey.Copy) and self.proc and self.proc.state()!=QProcess.ProcessState.NotRunning and not self.command.hasSelectedText():
                self.stop();return True
        return super().eventFilter(obj,event)
    def run(self):
        cmd=self.command.text().strip()
        if not cmd or (self.proc and self.proc.state()!=QProcess.ProcessState.NotRunning):return
        if QMessageBox.question(self,'Approve terminal command',f'Run this command on your computer?\n\n{cmd}\n\nCommands can modify files or system settings.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        # Directory changes are built-in so they persist between QProcess runs.
        import re
        cd_match=re.fullmatch(r'(?:cd|Set-Location|sl)(?:\s+(.*))?',cmd,re.I)
        if cd_match:
            target=(cd_match.group(1) or str(Path.home())).strip().strip('\"').strip("'")
            if target in ('..','.'): target=str(self.cwd/target)
            elif target=='~': target=str(Path.home())
            candidate=Path(target).expanduser()
            if not candidate.is_absolute():candidate=self.cwd/candidate
            candidate=candidate.resolve()
            if candidate.is_dir():
                self.cwd=candidate
                self.output.appendPlainText('> '+cmd+'\n'+str(self.cwd))
                self.command.clear()
            else:self.output.appendPlainText('Directory does not exist: '+str(candidate))
            return
        self.proc=QProcess(self);self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        if sys.platform=='win32':self.proc.setProgram('powershell.exe');self.proc.setArguments(['-NoProfile','-Command',cmd])
        else:self.proc.setProgram('/bin/sh');self.proc.setArguments(['-c',cmd])
        if not self.cwd.is_dir(): self.cwd=Path.home()
        self.proc.setWorkingDirectory(str(self.cwd))
        self.command_history.append(cmd);self.history_index=len(self.command_history)
        self.command.clear()
        self.output.appendPlainText('\n> '+cmd);self.run_button.setEnabled(False)
        self.proc.readyReadStandardOutput.connect(lambda:self.output.appendPlainText(bytes(self.proc.readAllStandardOutput()).decode(errors='replace').rstrip()))
        self.proc.finished.connect(lambda code,status:(self.output.appendPlainText(f'[Exit code {code}]'),self.run_button.setEnabled(True),self.command.setFocus()))
        self.proc.errorOccurred.connect(lambda error:self.output.appendPlainText('Process error: '+self.proc.errorString()))
        self.proc.start()
    def stop(self):
        if self.proc and self.proc.state()!=QProcess.ProcessState.NotRunning:self.proc.kill()
