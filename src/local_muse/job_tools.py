"""Local resume selection and opt-in job page retrieval."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse
import requests
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QKeySequence
from bs4 import BeautifulSoup

URL_RE = re.compile(r'https?://[^\s<>"\']+', re.I)


def extract_links(text):
    return list(dict.fromkeys(x.rstrip('.,);]') for x in URL_RE.findall(text)))[:30]


class JobLinksEdit(QPlainTextEdit):
    def insertFromMimeData(self, source):
        if source.hasText():
            pasted=source.text()
            links=extract_links(pasted)
            if links and not pasted.strip().replace('\n',' ').startswith('JOB:'):
                cursor=self.textCursor()
                if cursor.positionInBlock():cursor.insertText('\n')
                cursor.insertText('\n'.join(links)+'\n')
                self.setTextCursor(cursor)
                return
        super().insertFromMimeData(source)


class ResumeLibrary:
    def __init__(self):
        self.path=Path.home()/'.luclid-ii'/'resume_library.json'
    def save(self,path):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps({'latest':str(Path(path).resolve())}),encoding='utf-8')
    def latest(self):
        try:
            path=json.loads(self.path.read_text(encoding='utf-8'))['latest']
            return path if Path(path).is_file() else None
        except (OSError,ValueError,KeyError):return None


def fetch_job_page(url):
    parsed=urlparse(url)
    if parsed.scheme!='https' or not parsed.hostname:
        raise ValueError('Only HTTPS job links are supported')
    # No redirects to arbitrary hosts; refuse private network addresses to avoid SSRF.
    import ipaddress,socket
    def check(host):
        for info in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM):
            ip=ipaddress.ip_address(info[4][0])
            if not ip.is_global:raise ValueError('Private or local network addresses are blocked')
    check(parsed.hostname)
    response=requests.get(url,timeout=12,headers={'User-Agent':'Mozilla/5.0 (compatible; Luclid-ii/0.4.0)'},allow_redirects=False,stream=True)
    try:
        if response.status_code in (301,302,303,307,308):raise ValueError('Redirected page: open in browser and paste the final URL')
        response.raise_for_status()
        if 'text/html' not in response.headers.get('Content-Type',''):
            raise ValueError('Page did not return HTML')
        body=b''
        for chunk in response.iter_content(8192):
            body+=chunk
            if len(body)>1_000_000:raise ValueError('Page exceeds 1 MB limit')
        soup=BeautifulSoup(body,'html.parser')
        title=soup.title.get_text(' ',strip=True) if soup.title else 'Job posting'
        for tag in soup(['script','style','nav','footer','header']):tag.decompose()
        text=' '.join(soup.stripped_strings)[:16000]
        if len(text)<180:raise ValueError('Job description unavailable or login required')
        return title,text
    finally:response.close()


class JobFetchWorker(QObject):
    finished=Signal(object)
    def __init__(self,urls):
        super().__init__();self.urls=urls
    def run(self):
        results=[]
        for url in self.urls:
            try:
                title,text=fetch_job_page(url)
                results.append({'url':url,'title':title,'text':text,'error':None})
            except Exception as exc:
                results.append({'url':url,'title':'','text':'','error':str(exc)})
        self.finished.emit(results)


def score_match(resume,job):
    stop={'this','that','with','from','have','your','will','work','what','when','where','their','they','about','and','the','for','are','you','our','job','role','team'}
    words=lambda s:set(w for w in re.findall(r'[a-z][a-z0-9+#.-]{2,}',s.lower()) if w not in stop)
    wanted=words(job)
    return round(100*len(words(resume)&wanted)/len(wanted)) if wanted else 0


def categorize_score(score):
    if score>=35:return 'Strong Match'
    if score>=20:return 'Good Match'
    return 'Stretch Role'
