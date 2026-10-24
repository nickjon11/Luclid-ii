"""Optional, consent-driven application form helper. Never clicks Submit/Apply."""
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from .documents import extract_text, validate_file


def resume_fields(path):
    validate_file(path)
    text=extract_text(path)
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    email=re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',text)
    phone=re.search(r'(?<!\d)(?:\+1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)',text)
    # Name is only used if a plausible standalone header appears on the first few lines.
    name=''
    for line in lines[:4]:
        if re.fullmatch(r"[A-Za-z][A-Za-z'.-]+(?:\s+[A-Za-z][A-Za-z'.-]+){1,3}",line):
            name=line;break
    parts=name.split() if name else []
    return {'full_name':name,'first_name':parts[0] if parts else '',
            'last_name':parts[-1] if len(parts)>1 else '',
            'email':email.group(0) if email else '',
            'phone':phone.group(0) if phone else ''}


def main():
    if len(sys.argv)!=3:
        print('Usage: python -m local_muse.application_fill HTTPS_URL RESUME_PATH');return 2
    url,path=sys.argv[1:]
    parsed=urlparse(url)
    if parsed.scheme!='https' or not parsed.hostname:
        print('Only HTTPS application URLs are accepted.');return 2
    data=resume_fields(path)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('Install optional browser helper: pip install playwright; python -m playwright install chromium');return 2
    # We only fill clearly identified basic contact fields; no guesses for legal/eligibility questions.
    mapping={
        'first_name': ['first name','given name','firstname'],
        'last_name': ['last name','family name','surname','lastname'],
        'full_name': ['full name','your name','applicant name'],
        'email': ['email address','email'],
        'phone': ['phone number','mobile number','telephone','phone'],
    }
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=False)
        page=browser.new_page()
        try:
            page.goto(url,wait_until='domcontentloaded',timeout=45000)
            print('Review the site and log in manually if required. Autofill starts in 8 seconds.')
            page.wait_for_timeout(8000)
            filled=[]
            for key,labels in mapping.items():
                if not data[key]:continue
                for label in labels:
                    try:
                        field=page.get_by_label(re.compile(r'^'+re.escape(label)+r'$',re.I)).first
                        if field.count() and field.is_visible() and field.is_enabled():
                            if not field.input_value().strip():
                                field.fill(data[key]);filled.append(key)
                            break
                    except Exception:
                        continue
            # HTML input types are reliable fallbacks for email and telephone.
            for key,selector in [('email','input[type=email]'),('phone','input[type=tel]')]:
                if not data[key]:continue
                try:
                    field=page.locator(selector).first
                    if field.count() and field.is_visible() and not field.input_value().strip():
                        field.fill(data[key]);filled.append(key)
                except Exception:pass
            print('Filled fields:',', '.join(dict.fromkeys(filled)) or 'none (fill manually)')
            print('NO application has been submitted. Review and submit yourself if appropriate.')
            while browser.is_connected():
                try:page.wait_for_timeout(1000)
                except Exception:break
        except Exception as exc:
            print('Browser helper error:',exc)
            return 1
        finally:
            try:browser.close()
            except Exception:pass
    return 0


if __name__=='__main__':raise SystemExit(main())
