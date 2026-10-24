from pathlib import Path

ALLOWED={'.pdf','.docx','.txt','.md','.py','.json','.csv','.log'}
MAX_BYTES=8*1024*1024
MAX_CHARS=18000

def validate_file(path):
    p=Path(path)
    if p.suffix.lower() not in ALLOWED:raise ValueError('Unsupported file type: '+p.suffix)
    if not p.is_file():raise ValueError('File does not exist')
    if p.stat().st_size>MAX_BYTES:raise ValueError('File exceeds 8 MB limit')
    return p

def extract_text(path):
    p=validate_file(path)
    if p.suffix.lower()=='.pdf':
        from pypdf import PdfReader
        with p.open('rb') as f:
            reader=PdfReader(f)
            content='\n'.join(page.extract_text() or '' for page in reader.pages[:30])
    elif p.suffix.lower()=='.docx':
        from docx import Document
        content='\n'.join(x.text for x in Document(str(p)).paragraphs)
    else:
        content=p.read_text(encoding='utf-8',errors='replace')
    if not content.strip():raise ValueError('No extractable text found (scanned PDFs need OCR)')
    return content[:MAX_CHARS]+('\n[Truncated to fit local model context]' if len(content)>MAX_CHARS else '')
