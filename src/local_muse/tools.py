import platform
import os
import socket
import subprocess
import datetime
import psutil
from pathlib import Path
import requests

DESCRIPTIONS = {
    'system_info': 'Detailed operating system, CPU, RAM, GPU, disks, network and uptime report',
    'list_files': 'List files inside the selected workspace',
    'read_file': 'Read a UTF-8 text file inside the selected workspace (max 20 KB)',
    'search_files': 'Search filenames inside the selected workspace (max 100 matches)',
    'github_repo': 'Fetch public GitHub repository metadata (requires internet)',
}

def available_tools():
    return dict(DESCRIPTIONS)

def safe_path(workspace, relative):
    if not workspace:
        raise ValueError('Choose a workspace first.')
    root = Path(workspace).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Workspace must be a directory.')
    path = (root / (relative or '.')).resolve(strict=True)
    if not path.is_relative_to(root):
        raise ValueError('Access outside the selected workspace is blocked.')
    return path

def execute_tool(name, workspace=None, argument=''):
    if name == 'system_info':
        return detailed_system_info()
    if name == 'list_files':
        folder = safe_path(workspace, argument)
        if not folder.is_dir():
            raise ValueError('Not a directory.')
        return '\n'.join(('[DIR] ' if p.is_dir() else '[FILE] ') + p.name for p in sorted(folder.iterdir(), key=lambda p:p.name.lower())[:50]) or 'Empty folder.'
    if name == 'read_file':
        if not argument.strip() or argument.strip() == '.':
            raise ValueError('Specify a relative filename.')
        file = safe_path(workspace, argument)
        if not file.is_file() or file.stat().st_size > 20_000:
            raise ValueError('File must be a regular text file no larger than 20 KB.')
        return file.read_text(encoding='utf-8')
    if name == 'search_files':
        if not argument.strip():
            raise ValueError('Enter a filename search term.')
        root = safe_path(workspace, '.')
        matches = []
        for p in root.rglob('*'):
            if len(matches) >= 100:
                break
            if p.is_symlink():
                continue
            if argument.casefold() in p.name.casefold():
                matches.append(str(p.relative_to(root)))
        return '\n'.join(matches) or 'No matching filenames.'
    if name == 'github_repo':
        import re
        username = argument.strip()
        if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?', username):
            raise ValueError('Enter a GitHub username only.')
        response = requests.get(f'https://api.github.com/users/{username}/repos',
            params={'per_page':100,'sort':'updated'},
            headers={'Accept':'application/vnd.github+json'}, timeout=15)
        response.raise_for_status()
        repos=response.json()
        if not isinstance(repos,list):raise ValueError('Unexpected GitHub response.')
        return ('Public repositories for '+username+':\n'+
                '\n'.join(f"{repo['full_name']} — {repo.get('description') or 'No description'} — {repo['html_url']}" for repo in repos)
                if repos else 'No public repositories found.')
    raise ValueError('Unknown tool.')


def _windows_cim(class_name, fields):
    """Read-only Windows CIM query, no shell and no PowerShell profile."""
    if platform.system() != 'Windows':
        return []
    import json
    fieldlist = ','.join(fields)
    cmd = ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
           f'Get-CimInstance -ClassName {class_name} | Select-Object {fieldlist} | ConvertTo-Json -Compress']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=9,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode != 0 or not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        return data if isinstance(data, list) else [data]
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []


def detailed_system_info():
    """Read-only diagnostics; unavailable values are clearly identified."""
    lines = ['SYSTEM INFORMATION', '==================',
             f'OS: {platform.platform()}',
             f'OS release: {platform.release()}',
             f'Architecture: {platform.machine()} / {platform.architecture()[0]}',
             f'Python: {platform.python_version()}',
             '', 'PROCESSOR']
    cpu = _windows_cim('Win32_Processor', ['Name','Manufacturer','NumberOfCores','NumberOfLogicalProcessors'])
    info = cpu[0] if cpu else {}
    lines += [f'Model: {info.get("Name") or platform.processor() or "Unavailable"}',
              f'Manufacturer: {info.get("Manufacturer") or "Unavailable"}',
              f'Physical cores: {info.get("NumberOfCores") or psutil.cpu_count(logical=False) or "Unavailable"}',
              f'Logical processors: {info.get("NumberOfLogicalProcessors") or psutil.cpu_count(logical=True) or "Unavailable"}',
              '', 'MEMORY']
    mem = psutil.virtual_memory()
    gib = lambda v: f'{v / (1024 ** 3):.2f} GiB'
    lines += [f'Total RAM: {gib(mem.total)}', f'Available RAM: {gib(mem.available)}',
              f'RAM usage: {mem.percent}%', '', 'GRAPHICS']
    gpu = _windows_cim('Win32_VideoController', ['Name','AdapterRAM','DriverVersion'])
    if gpu:
        for g in gpu:
            lines.append(f'GPU: {g.get("Name") or "Unknown"} | Driver: {g.get("DriverVersion") or "Unavailable"}')
        lines.append('GPU VRAM: Not reliably available from Windows CIM; use vendor tools for accurate VRAM.')
    elif platform.system() == 'Darwin':
        try:
            r = subprocess.run(['system_profiler','SPDisplaysDataType'],capture_output=True,text=True,timeout=8)
            lines += [r.stdout.strip()[:1800] or 'Unavailable']
        except (OSError,subprocess.TimeoutExpired): lines += ['Unavailable']
    elif platform.system() == 'Linux':
        try:
            r = subprocess.run(['lspci'],capture_output=True,text=True,timeout=5)
            lines += [line.strip() for line in r.stdout.splitlines() if 'VGA' in line or '3D controller' in line] or ['Unavailable']
        except (OSError,subprocess.TimeoutExpired): lines += ['Unavailable']
    else: lines += ['Unavailable on this platform']
    lines += ['', 'STORAGE']
    seen = set()
    for disk in psutil.disk_partitions(all=False):
        if disk.mountpoint in seen: continue
        seen.add(disk.mountpoint)
        try:
            u = psutil.disk_usage(disk.mountpoint)
            lines.append(f'{disk.device} ({disk.mountpoint}): {gib(u.total)} total, {gib(u.free)} free, {u.percent}% used')
        except (OSError, PermissionError): continue
    lines += ['', 'MOTHERBOARD / FIRMWARE']
    boards = _windows_cim('Win32_BaseBoard',['Manufacturer','Product'])
    bios = _windows_cim('Win32_BIOS',['SMBIOSBIOSVersion'])
    if boards: lines.append(f'Motherboard: {boards[0].get("Manufacturer") or "Unknown"} {boards[0].get("Product") or ""}')
    else: lines.append('Motherboard: Unavailable')
    lines.append(f'BIOS/UEFI: {bios[0].get("SMBIOSBIOSVersion") or "Unavailable"}' if bios else 'BIOS/UEFI: Unavailable')
    lines += ['', 'NETWORK (local interface addresses only)']
    for interface, addresses in psutil.net_if_addrs().items():
        ips = [a.address for a in addresses if a.family in (socket.AF_INET,socket.AF_INET6) and not a.address.startswith(('127.','::1','fe80:'))]
        if ips: lines.append(f'{interface}: {", ".join(ips[:3])}')
    lines += ['', 'UPTIME', f'Last boot: {datetime.datetime.fromtimestamp(psutil.boot_time()).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")}']
    return '\n'.join(lines)
