from environs import environment
import requests
import random
import string
import time


headers = {
    'Content-Type': 'application/json'
}

def notify(phone_number, msg):
    phone_number_format = f'26{phone_number}'
    timestamp = int(time.time() * 1000)
    random_component = random.randint(1000, 9999)
    msg_ref = f'{timestamp}{random_component}'
  
    payload = {
        'username': environment.env_vars.get('PROBASE_USERNAME'),
        'password': environment.env_vars.get('PROBASE_PASSWORD'),
        'senderid': environment.env_vars.get('PROBASE_SENDER_ID'),
        'source': environment.env_vars.get('PROBASE_SOURCE'),
        'recipient': [phone_number_format],
        'message': f'{msg}',
        'msg_ref': msg_ref,
    }

    try:
        response = requests.post(f"{environment.env_vars.get('PROBASE_URL')}", json=payload, headers=headers)
        results = response.text
        print(results)
        return results
    except Exception as e:
        print(str(e))
        return None