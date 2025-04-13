########### IMPORTS ###########
import os
import sys
import math
import requests
import logging
from datetime import datetime

########### VARIABLES ###########
BOT_TOKEN = os.environ.get("BOT_TOKEN", "botToken_123")
ALLOWED_USERNAMES = os.environ.get('ALLOWED_USERNAMES', '@nouser').split(',')
AWG_URL = os.environ.get("AWG_URL", 'http://wg.example.com:52820')
AWG_PASSWORD = os.environ.get("AWG_PASSWORD", "password")
BACKUP_PATH = os.environ.get("BACKUP_PATH", "/opt/app")

# Set up logging to catch errors and info messages
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

########### SCRIPTS ###########
def pages_count(list, group_size=5):
    total_items = len(list)
    return math.ceil(total_items / group_size)

########### SCRIPTS ###########
# Make sure to update the password to the password you set for your webgui
def get_session_id(base_url=AWG_URL):
    path = base_url + '/api/session'

    headers = {'Content-Type': 'application/json'}
    data = f'{{"password": "{AWG_PASSWORD}"}}'

    # Make initial request to obtain session ID
    response = requests.post(path, headers=headers, data=data)

    # Extract session ID from Set-Cookie header
    session_id = response.cookies.get('connect.sid')
    return session_id

def get_peers(base_url=AWG_URL):
    session_id=get_session_id()
    # Make second request with session ID in Cookie header
    path = base_url + '/api/wireguard/client'

    headers = {'Cookie': f'connect.sid={session_id}'}
    response = requests.get(path, headers=headers)

    # Check if the request was successful and print peer data
    if response.status_code == 200:
        return response.json()
    else:
        return  f'Error: {response.status_code} - {response.text}'

def delete_peer(peer_id, base_url=AWG_URL):
    session_id=get_session_id()
    # Make second request with session ID in Cookie header
    path = base_url + '/api/wireguard/client/' + peer_id

    headers = {'Cookie': f'connect.sid={session_id}'}
    response = requests.delete(path, headers=headers)

    # Check if the request was successful and print peer data
    if response.status_code == 200:
        return True
    else:
        return f'Error: {response.status_code} - {response.text}'
    
def disable_peer(peer_id, base_url=AWG_URL):
    session_id=get_session_id()
    # Make second request with session ID in Cookie header
    path = base_url + '/api/wireguard/client/' + peer_id + '/disable'

    headers = {'Cookie': f'connect.sid={session_id}'}
    response = requests.post(path, headers=headers)

    # Check if the request was successful and print peer data
    if response.status_code == 200:
        return True
    else:
        return f'Error: {response.status_code} - {response.text}'

def enable_peer(peer_id, base_url=AWG_URL):
    session_id=get_session_id()
    # Make second request with session ID in Cookie header
    path = base_url + '/api/wireguard/client/' + peer_id + '/enable'

    headers = {'Cookie': f'connect.sid={session_id}'}
    response = requests.post(path, headers=headers)

    # Check if the request was successful and print peer data
    if response.status_code == 200:
        return True
    else:
        return f'Error: {response.status_code} - {response.text}'

def extract_peer_data(peer_data, page_number, session_id=get_session_id()):
    # peer_data=get_peers()
    peer_data=[peer_data[i:i + 5] for i in range(0, len(peer_data), 5)]
    
    result = f'<strong>Peers total:</strong> {len(peer_data)*5}\n\n'
    for peer in peer_data[int(page_number)]:
        # Convert transfer values from bytes to MBytes
        transfer_rx_mb = peer['transferRx'] / (1024 ** 2) if peer['transferRx'] else 0
        transfer_tx_mb = peer['transferTx'] / (1024 ** 2) if peer['transferTx'] else 0

        # Convert latestHandshakeAt to the desired format
        latest_handshake = datetime.strptime(peer['latestHandshakeAt'], "%Y-%m-%dT%H:%M:%S.%fZ") if peer['latestHandshakeAt'] else 'N/A'

        result += f"<strong>Name:</strong> {peer['name']}\n"
        result += f"Address: `{peer['address']}`\n"
        result += f"<blockquote expandable><strong>Extended Information:</strong>\n"
        result += f"- ID: `{peer['id']}`\n"
        result += f"- Enabled: `{peer['enabled']}`\n"
        result += f"- Latest Handshake At: `{latest_handshake}`\n\n"
        result += f"<strong>Transfer Data:</strong>\n"
        result += f"- Transfer TX: `{transfer_tx_mb:.2f} MB`\n"
        result += f"- Transfer RX: `{transfer_rx_mb:.2f} MB`\n"
        result += f"- Created At: `{peer['createdAt']}`\n"
        result += f"- Updated At: `{peer['updatedAt']}`\n"
        result += f"- Expired At: `{peer['expiredAt'] if peer['expiredAt'] else 'N/A'}`</blockquote>"

    result += f'\n\n<strong>Page:</strong> {int(page_number)+1}'

    return result

def create_new_peer(peer_name, base_url=AWG_URL, session_id=get_session_id()):
    # Make third request with session ID in Cookie header and provide a name for the new peer to be created
    path = base_url + '/api/wireguard/client'
    name = peer_name
    headers = {'Content-Type': 'application/json', 'Cookie': f'connect.sid={session_id}'}
    data = '{"name":"'+name+'"}'
    response = requests.post(path, headers=headers, data=data)

    # Check if the request was successful and print new peer data
    if response.status_code == 200:

        peer_data = get_peers()

        for peer in peer_data:
            if peer.get("name") == name:
                peer_id = peer.get("id")
                break
        
        return {"filename" : f'{name}.conf', "file" : get_peer_config(peer_id)}
    else:
        return f'Error: {response.status_code} - {response.text}'

def get_peer_config(peer_id, base_url=AWG_URL, session_id=get_session_id()):
    # Make third request with session ID in Cookie header and provide a name for the new peer to be created
    path = base_url + '/api/wireguard/client/' + peer_id + '/configuration'
    headers = {'Content-Type': 'application/json', 'Cookie': f'connect.sid={session_id}'}
    response = requests.get(path, headers=headers)

    # Check if the request was successful and print new peer data
    if response.status_code == 200:
        return response.content
    else:
        return "Error fetching file."
    
def create_backup(base_url=AWG_URL, session_id=get_session_id()):
    path = base_url + '/api/wireguard/backup'
    headers = {'Content-Type': 'application/json', 'Cookie': f'connect.sid={session_id}'}
    response = requests.get(path, headers=headers)

    try:
        response = requests.get(path, headers=headers)

        if response.status_code == 200:
            # Ensure the backup path exists
            os.makedirs(BACKUP_PATH, exist_ok=True)

            # Write the response content to a file
            backup_file_path = os.path.join(BACKUP_PATH, 'wg0.json')
            with open(backup_file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f'Backup saved to {backup_file_path}')
            return f'Backup saved to {backup_file_path}'
        else:
            logger.error(f"Can't get backup from {base_url}, status code {response.status_code}")
            return f"Can't get backup from {base_url}, status code {response.status_code}"
    
    except requests.RequestException as e:
        logger.error(f"An error occurred while fetching the backup: {str(e)}")
        return f"An error occurred while fetching the backup: {str(e)}"

def get_qr(peer_id, base_url=AWG_URL, session_id=get_session_id()):
    # Make third request with session ID in Cookie header and provide a name for the new peer to be created
    path = base_url + '/api/wireguard/client/' + peer_id + '/qrcode.svg'
    headers = {'Content-Type': 'application/json', 'Cookie': f'connect.sid={session_id}'}
    response = requests.get(path, headers=headers)

    # Check if the request was successful and print new peer data
    if response.status_code == 200:
        print(response.text)
    else:
        print(f'Error: {response.status_code} - {response.text}')