"""Google OAuth desktop integration; API requests are made only when requested."""
import base64
import hashlib
import json
import secrets
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode, urlparse, parse_qs
import keyring
import requests

SERVICE = 'Luclid-ii-Google'
SCOPES = {
    'calendar_read': 'https://www.googleapis.com/auth/calendar.readonly',
    'calendar_write': 'https://www.googleapis.com/auth/calendar.events',
    'gmail_read': 'https://www.googleapis.com/auth/gmail.readonly',
    'gmail_compose': 'https://www.googleapis.com/auth/gmail.compose',
    'gmail_send': 'https://www.googleapis.com/auth/gmail.send',
}

class GoogleAccount:
    def __init__(self):
        self.session = requests.Session()

    def _load(self):
        try:
            return json.loads(keyring.get_password(SERVICE, 'oauth') or '{}')
        except (ValueError, KeyError):
            return {}

    def _save(self, data):
        keyring.set_password(SERVICE, 'oauth', json.dumps(data))

    def connected(self):
        return bool(self._load().get('refresh_token') or self._load().get('access_token'))

    def disconnect(self):
        try: keyring.delete_password(SERVICE, 'oauth')
        except keyring.errors.PasswordDeleteError: pass

    def connect(self, client_id, requested_scopes, timeout=180, client_secret=""):
        """Browser OAuth with PKCE and loopback callback; call from a worker thread."""
        if not client_id.strip(): raise ValueError('Google OAuth Desktop client ID is required.')
        scopes = [SCOPES[k] for k in requested_scopes if k in SCOPES]
        if not scopes: raise ValueError('Choose at least one permission.')
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
        state = secrets.token_urlsafe(32)
        result = {}
        signal = threading.Event()
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                params = parse_qs(urlparse(self.path).query)
                if params.get('state', [''])[0] != state:
                    result['error'] = 'OAuth state validation failed.'
                elif 'error' in params:
                    result['error'] = params['error'][0]
                else:
                    result['code'] = params.get('code', [''])[0]
                message = b'<h3>Luclid-ii authorization received. You can close this tab.</h3>'
                self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers(); self.wfile.write(message)
                signal.set()
            def log_message(self, *_): pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        server.timeout = 1
        redirect = f'http://127.0.0.1:{server.server_port}/'
        params = {'client_id':client_id.strip(), 'redirect_uri':redirect, 'response_type':'code',
                  'scope':' '.join(scopes), 'access_type':'offline', 'prompt':'consent',
                  'state':state, 'code_challenge':challenge, 'code_challenge_method':'S256'}
        webbrowser.open('https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params))
        deadline = time.monotonic() + timeout
        try:
            while not signal.is_set() and time.monotonic() < deadline: server.handle_request()
        finally:
            server.server_close()
        if not signal.is_set(): raise TimeoutError('Google sign-in timed out.')
        if result.get('error'): raise ValueError(result['error'])
        if not result.get('code'): raise ValueError('No authorization code received.')
        response = self.session.post('https://oauth2.googleapis.com/token', data={
            'client_id':client_id.strip(), 'code':result['code'], 'code_verifier':verifier,
            'redirect_uri':redirect, 'grant_type':'authorization_code',
            **({'client_secret': client_secret.strip()} if client_secret.strip() else {})}, timeout=25)
        self._check_oauth_response(response)
        token = response.json()
        old = self._load()
        self._save({'client_id':client_id.strip(), 'access_token':token['access_token'],
                    'refresh_token':token.get('refresh_token', old.get('refresh_token')),
                    'client_secret':client_secret.strip(),
                    'expires_at':time.time()+token.get('expires_in', 3600)-60,
                    'scopes':token.get('scope',' '.join(scopes)).split()})

    @staticmethod
    def _check_oauth_response(response):
        if response.ok:
            return
        try:
            body = response.json()
            reason = body.get('error', 'unknown_error')
            detail = body.get('error_description', '')
        except (ValueError, AttributeError):
            reason, detail = 'http_error', 'Google rejected the OAuth request.'
        # Never expose access tokens, authorization codes, or submitted credentials.
        raise RuntimeError(f'Google OAuth ({response.status_code}): {reason}' +
                           (f' — {detail[:250]}' if detail else ''))

    def _token(self, scope=None):
        data = self._load()
        if not data: raise RuntimeError('Connect your Google Account first.')
        if scope and scope not in data.get('scopes', []):
            raise PermissionError('This action requires additional Google permissions. Reconnect and enable them.')
        if data.get('expires_at',0) > time.time(): return data['access_token']
        if not data.get('refresh_token'): raise RuntimeError('Google session expired. Reconnect your account.')
        response = self.session.post('https://oauth2.googleapis.com/token', data={
            'client_id':data['client_id'], 'refresh_token':data['refresh_token'],
            'grant_type':'refresh_token',
            **({'client_secret':data['client_secret']} if data.get('client_secret') else {})}, timeout=25)
        self._check_oauth_response(response)
        token = response.json()
        data['access_token'] = token['access_token']
        data['expires_at'] = time.time()+token.get('expires_in',3600)-60
        self._save(data)
        return data['access_token']

    def request(self, method, url, scope, **kwargs):
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = 'Bearer ' + self._token(SCOPES[scope])
        response = self.session.request(method, url, headers=headers, timeout=25, **kwargs)
        if not response.ok:
            try: detail = response.json().get('error',{}).get('message', response.text[:200])
            except ValueError: detail = response.text[:200]
            raise RuntimeError(f'Google API ({response.status_code}): {detail}')
        return response.json() if response.content else {}

    def calendars(self):
        return self.request('GET','https://www.googleapis.com/calendar/v3/users/me/calendarList','calendar_read').get('items',[])

    def events(self, calendar_id='primary', limit=30):
        from urllib.parse import quote
        url = 'https://www.googleapis.com/calendar/v3/calendars/' + quote(calendar_id,safe='') + '/events'
        return self.request('GET',url,'calendar_read',params={
            'timeMin':datetime.now(timezone.utc).isoformat(), 'maxResults':limit,
            'singleEvents':'true','orderBy':'startTime'}).get('items',[])

    def create_event(self, title, start_iso, end_iso, calendar_id='primary', description=''):
        from urllib.parse import quote
        url='https://www.googleapis.com/calendar/v3/calendars/'+quote(calendar_id,safe='')+'/events'
        return self.request('POST',url,'calendar_write',json={'summary':title,'description':description,
            'start':{'dateTime':start_iso},'end':{'dateTime':end_iso}})

    def inbox(self, limit=20, label="INBOX"):
        result = self.request('GET','https://gmail.googleapis.com/gmail/v1/users/me/messages',
                              'gmail_read',params={'maxResults':limit,'labelIds':label})
        items=[]
        for msg in result.get('messages',[]):
            detail=self.request('GET','https://gmail.googleapis.com/gmail/v1/users/me/messages/'+msg['id'],
                                'gmail_read',params={'format':'metadata','metadataHeaders':['From','Subject','Date']})
            headers={h['name'].lower():h['value'] for h in detail.get('payload',{}).get('headers',[])}
            items.append({'id':msg['id'],'from':headers.get('from',''), 'subject':headers.get('subject','(no subject)'),
                          'date':headers.get('date',''), 'snippet':detail.get('snippet','')})
        return items

    def email(self, message_id):
        return self.request('GET','https://gmail.googleapis.com/gmail/v1/users/me/messages/'+message_id,
                            'gmail_read',params={'format':'full'})

    def send_email(self, to, subject, body):
        from email.message import EmailMessage
        message=EmailMessage();message['To']=to;message['Subject']=subject;message.set_content(body)
        raw=base64.urlsafe_b64encode(message.as_bytes()).decode()
        return self.request('POST','https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
                            'gmail_send',json={'raw':raw})
