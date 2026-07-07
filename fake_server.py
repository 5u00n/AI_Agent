
import json
import sys

def write_log(s):
    with open('log.txt', 'a') as f:
        f.write(s + '\n')

def read_message():
    line = sys.stdin.readline()
    write_log(f"Line: {line}")
    if not line:
        return None
    return json.loads(line)

def write_message(obj):
    sys.stdout.write(json.dumps(obj) + '\n')
    sys.stdout.flush()

while True:
    try:
        req = read_message()
    except Exception as e:
        write_log(str(e))
        break
    if req is None:
        break
    method = req.get('method')
    if method == 'initialize':
        write_message({'jsonrpc': '2.0', 'id': req['id'], 'result': {'capabilities': {}, 'protocolVersion': '2024-11-05', 'serverInfo': {'name': 'test', 'version': '1.0'}}})
    elif method == 'notifications/initialized':
        pass
    elif method == 'tools/call':
        params = req.get('params', {})
        write_message({
            'jsonrpc': '2.0',
            'id': req['id'],
            'result': {
                'content': [{'type': 'text', 'text': json.dumps({'echo': params})}],
                'isError': False
            }
        })
    else:
        write_message({'jsonrpc': '2.0', 'id': req.get('id'), 'result': {'content': [], 'isError': False}})
