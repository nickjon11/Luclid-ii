import json
import requests

URL = 'http://127.0.0.1:11434/api/chat'
SYSTEM = ('You are Luclid-ii, an on-device assistant developed by Jonathan Lachman. '
          'Your language model is provided by Ollama, not a custom model created by the Luclid-ii developer. '
          'Do not invent your creator, capabilities, internet access, or tool results. '
          'Only say a task was completed when an actual tool result confirms it.')

def call(model, messages, system=SYSTEM, timeout=240):
    response = requests.post(URL, json={'model':model,'stream':False,'messages':[{'role':'system','content':system},*messages], 'options':{'temperature':0.3}},timeout=timeout)
    if response.status_code == 404:
        raise RuntimeError('Model not found. Run ollama list and check the model field.')
    response.raise_for_status()
    return response.json()['message']['content']

def chat(model, messages):
    return call(model, messages)

def plan(model, messages, tools):
    descriptions = '\n'.join(f'{name}: {description}' for name, description in tools.items())
    system = SYSTEM + """
Choose whether ONE tool is necessary to answer the last user request.
Tools:
""" + descriptions + """
Respond ONLY with JSON: {"tool":"none|tool_name","argument":"relative file path, search term, or GitHub username","reason":"short reason"}.
Use none for ordinary conversation, drafting, and questions that do not need live local data.
Never invent a filename. If information is missing, choose none and ask the user for it.
For github_repo, only use a clearly specified GitHub username.
For read_file, use only a file path explicitly provided by the user.
"""
    raw = call(model, messages[-4:], system, timeout=90).strip()
    try:
        if raw.startswith('```'):
            raw = raw.split('\n',1)[1].rsplit('```',1)[0]
        data = json.loads(raw)
        if data.get('tool') not in [*tools, 'none']:
            return {'tool':'none','argument':'','reason':''}
        return {'tool':data['tool'],'argument':str(data.get('argument','')),'reason':str(data.get('reason',''))}
    except (ValueError, TypeError):
        return {'tool':'none','argument':'','reason':''}
