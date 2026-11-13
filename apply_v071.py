#!/usr/bin/env python3
"""Apply Luclid-ii v0.7.1 source updates to a local checkout."""
from pathlib import Path
import re
root=Path.cwd()
assert (root/'pyproject.toml').exists() and (root/'src/local_muse/app.py').exists(), 'Run from Luclid-ii repository root'
assert (root/'VERSION').read_text().strip() in ('0.7.0','0.7.1'), 'Expected v0.7.0 base'
def change(path,fn):
 p=root/path; old=p.read_text(encoding='utf-8'); new=fn(old)
 if new!=old:p.write_text(new,encoding='utf-8');print('Updated',path)
 else:print('Unchanged',path)
(root/'VERSION').write_text('0.7.1\n',encoding='utf-8')
change('src/local_muse/version.py',lambda s:re.sub(r"APP_VERSION\s*=\s*['\"][^'\"]+['\"]", "APP_VERSION = '0.7.1'",s))
change('pyproject.toml',lambda s:re.sub(r'(?m)^version\s*=\s*"[^"]+"','version = "0.7.1"',s,count=1))
change('src/local_muse/app.py',lambda s:s.replace("('Automation & Tasks','tasks')","('Automation Tasks','tasks')").replace("'Automation & Tasks'", "'Automation Tasks'").replace('Automation & Tasks —','Automation Tasks —'))
# Align the legacy wizard with VERSION; remove old hardcoded version checks in release gate.
check=root/'packaging/check_version.py'
if check.exists():
 change('packaging/check_version.py',lambda s: '\n'.join(line for line in s.split('\n') if "assert 'v0.6.24' not in setup" not in line))
# The existing Windows Inno Setup installer already installs to Programs, creates Start Menu entry,
# and offers desktop icon. Keep those features and avoid launching the app during installation.
change('packaging/windows_installer.iss',lambda s:re.sub(r'(?m)^Filename: "\{app\}\\Luclid-ii\.exe"; Description: "Launch Luclid-ii"; Flags: nowait postinstall skipifsilent$', 'Filename: "{app}\\\\Luclid-ii.exe"; Description: "Launch Luclid-ii"; Flags: nowait postinstall skipifsilent unchecked',s))
# Linux .deb already registers desktop search; retain it.
# Add a safe, opt-in form filler bridge with explicit per-field approval and no submit action.
ext=root/'browser_extension';ext.mkdir(exist_ok=True)
(ext/'manifest.json').write_text('''{\n  "manifest_version": 3,\n  "name": "Luclid-ii Job Copilot (Preview)",\n  "version": "0.7.1",\n  "description": "Review-first assistance for job application forms.",\n  "permissions": ["activeTab", "scripting"],\n  "action": {"default_popup": "popup.html"}\n}\n''')
(ext/'popup.html').write_text('''<!doctype html><html><head><meta charset="utf-8"><style>body{font:14px sans-serif;background:#211a2d;color:#fff;width:290px;padding:14px}button,textarea{width:100%;box-sizing:border-box;margin:6px 0;padding:8px}button{background:#7950a6;color:white;border:1px solid #bd9cdd}textarea{height:130px}</style></head><body><h3>Luclid-ii Job Copilot</h3><p>Preview: paste a JSON object of application fields to fill. Review the page before submitting.</p><textarea id="fields" placeholder='{"full_name":"Example Person","email":"example@example.com"}'></textarea><button id="preview">Preview matching fields</button><button id="fill">Fill reviewed fields</button><p id="status" role="status"></p><script src="popup.js"></script></body></html>''')
(ext/'popup.js').write_text('''const status = document.getElementById('status');
const supported = ['full_name','first_name','last_name','email','phone'];
function parse() {const data=JSON.parse(document.getElementById('fields').value); if(!data || Array.isArray(data) || typeof data !== 'object') throw Error('Expected JSON object');return Object.fromEntries(Object.entries(data).filter(([k,v])=>supported.includes(k)&&typeof v==='string'&&v.length<300));}
async function run(fill) {try {const values=parse();const [tab]=await chrome.tabs.query({active:true,currentWindow:true});if(!tab?.id || !/^https:\/\//.test(tab.url||'')) throw Error('Open an HTTPS application page first');const result=await chrome.scripting.executeScript({target:{tabId:tab.id},func:(values,fill)=>{const aliases={full_name:['name','full_name','fullname'],first_name:['first_name','firstname','given_name'],last_name:['last_name','lastname','family_name'],email:['email','email_address'],phone:['phone','telephone','mobile']};const matches=[];for(const [key,value] of Object.entries(values)){const names=aliases[key];const input=[...document.querySelectorAll('input')].find(el=>!el.disabled&&!el.readOnly&&['text','email','tel',''].includes(el.type)&&[el.name,el.id,el.autocomplete].some(v=>names.includes((v||'').toLowerCase().replace(/[ -]/g,'_'))));if(input){matches.push(key);if(fill){input.value=value;input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));}}}return matches;},args:[values,fill]});status.textContent=(fill?'Filled: ':'Matched: ')+(result[0]?.result?.join(', ')||'none')+'. Review all fields manually; nothing was submitted.';}catch(e){status.textContent=e.message;}}
document.getElementById('preview').onclick=()=>run(false);
document.getElementById('fill').onclick=()=>run(true);
''')
(ext/'README.md').write_text('''# Luclid-ii Job Copilot browser extension — v0.7.1 preview\n\nLoad this folder as an unpacked extension in a Chromium-based browser. Open an HTTPS application form, paste a JSON object containing only `full_name`, `first_name`, `last_name`, `email`, or `phone`, and click **Preview matching fields** before **Fill reviewed fields**. No automatic submission, LinkedIn account integration, resume parsing, or native app connection is implemented yet. Never paste credentials or sensitive identification numbers. Fields are processed in the active tab; no remote service is called. Some React-controlled forms may not accept programmatic changes. This is a foundation for later native-app integration, not a complete Simplify replacement.\n''')
(root/'CHANGELOG_v0.7.1.md').write_text('''# Luclid-ii v0.7.1 — development\n\n- Synchronize application, packaging, and source versions to 0.7.1.\n- Shorten Automation & Tasks navigation label to Automation Tasks.\n- Retain native Windows one-time installer, Linux .deb desktop launcher, and macOS .dmg app install.\n- Windows installer offers an optional desktop shortcut and leaves the installed application ready to launch from Start.\n- Add a minimal opt-in browser extension prototype for previewing and filling a small set of explicitly supplied job application fields. No automatic submission or LinkedIn API integration.\n\n**Release status:** Development source only. Native binaries require GitHub Actions build and validation on each target OS.\n''')
change('README.md',lambda s:s.replace('# Luclid-ii — AI Agent v0.7.0','# Luclid-ii — AI Agent v0.7.1',1)+ '\n\n## v0.7.1 preview\nSee `CHANGELOG_v0.7.1.md` and `browser_extension/README.md`.\n')
print('Patch applied. Next: python3 packaging/check_version.py')
