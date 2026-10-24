import re
import requests
import keyring

SERVICE='Luclid-ii - AI Agent'
KEY='github_token'

def save_github_token(token):
    token=token.strip()
    if not token:raise ValueError('Token cannot be empty')
    keyring.set_password(SERVICE,KEY,token)

def has_github_token():
    return bool(keyring.get_password(SERVICE,KEY))

def remove_github_token():
    try:keyring.delete_password(SERVICE,KEY)
    except keyring.errors.PasswordDeleteError:pass

def github_get(repo):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):
        raise ValueError('Use owner/repository format')
    headers={'Accept':'application/vnd.github+json','User-Agent':'Luclid-ii/0.3.1'}
    token=keyring.get_password(SERVICE,KEY)
    if token:headers['Authorization']='Bearer '+token
    response=requests.get('https://api.github.com/repos/'+repo,headers=headers,timeout=12)
    response.raise_for_status()
    data=response.json()
    return f"{data.get('full_name')}\nDescription: {data.get('description') or 'None'}\nVisibility: {'private' if data.get('private') else 'public'}\nStars: {data.get('stargazers_count')}\nURL: {data.get('html_url')}"


def github_list_repos(username):
    """List public repos, or authenticated repos for the saved token's own account."""
    if not re.fullmatch(r'[A-Za-z0-9-]{1,39}',username):
        raise ValueError('Enter a valid GitHub username')
    headers={'Accept':'application/vnd.github+json','User-Agent':'Luclid-ii/0.3.3'}
    token=keyring.get_password(SERVICE,KEY)
    if token:headers['Authorization']='Bearer '+token
    endpoint='https://api.github.com/users/'+username+'/repos'
    if token:
        me=requests.get('https://api.github.com/user',headers=headers,timeout=15)
        if me.ok and me.json().get('login','').lower()==username.lower():
            endpoint='https://api.github.com/user/repos'
    response=requests.get(endpoint,params={'per_page':100,'sort':'updated','affiliation':'owner'},headers=headers,timeout=15)
    response.raise_for_status()
    return [{'full_name':x['full_name'],'html_url':x['html_url'],'private':x['private']} for x in response.json()]
