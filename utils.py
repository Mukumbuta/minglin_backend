import requests
import random
import string
import time
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger('api')

headers = {
    'Content-Type': 'application/json'
}

def notify(phone_number, msg):
    phone_number_format = f'26{phone_number}'
    timestamp = int(time.time() * 1000)
    random_component = random.randint(1000, 9999)
    msg_ref = f'{timestamp}{random_component}'
    
    username = os.getenv('PROBASE_USERNAME')
    password = os.getenv('PROBASE_PASSWORD')
    sender_id = os.getenv('PROBASE_SENDER_ID')
    url = os.getenv('PROBASE_URL')
    source = os.getenv('PROBASE_SOURCE')
  
    payload = {
        'username': username,
        'password': password,
        'senderid': sender_id,
        'source': source,
        'recipient': [phone_number_format],
        'message': f'{msg}',
        'msg_ref': msg_ref,
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        results = response.text
        logger.info(f"SMS sent successfully to {phone_number}: {results}")
        return results
    except Exception as e:
        logger.error(f"Error sending SMS to {phone_number}: {str(e)}")
        return None