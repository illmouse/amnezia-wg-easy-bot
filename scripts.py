import os
import requests
import logging
from dotenv import load_dotenv
from datetime import datetime
from bot import AWG_URL, AWG_PASSWORD, BACKUP_PATH

current_date = datetime.now().strftime("%Y_%m_%d")

# Set up logging to catch errors and info messages
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

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

def get_client(base_url=AWG_URL):
    session_id=get_session_id()
    # Make second request with session ID in Cookie header
    path = base_url + '/api/wireguard/client'

    headers = {'Cookie': f'connect.sid={session_id}'}
    response = requests.get(path, headers=headers)

    # Check if the request was successful and print client data
    if response.status_code == 200:
        return response.json()
    else:
        return  f'Error: {response.status_code} - {response.text}'

def delete_client(client_id, base_url=AWG_URL):
    session_id=get_session_id()
    # Make second request with session ID in Cookie header
    path = base_url + '/api/wireguard/client/' + client_id

    headers = {'Cookie': f'connect.sid={session_id}'}
    response = requests.delete(path, headers=headers)

    # Check if the request was successful and print client data
    if response.status_code == 200:
        return True
    else:
        return f'Error: {response.status_code} - {response.text}'
    
def disable_client(client_id, base_url=AWG_URL):
    session_id=get_session_id()
    # Make second request with session ID in Cookie header
    path = base_url + '/api/wireguard/client/' + client_id + '/disable'

    headers = {'Cookie': f'connect.sid={session_id}'}
    response = requests.post(path, headers=headers)

    # Check if the request was successful and print client data
    if response.status_code == 200:
        return True
    else:
        return f'Error: {response.status_code} - {response.text}'

def enable_client(client_id, base_url=AWG_URL):
    session_id=get_session_id()
    # Make second request with session ID in Cookie header
    path = base_url + '/api/wireguard/client/' + client_id + '/enable'

    headers = {'Cookie': f'connect.sid={session_id}'}
    response = requests.post(path, headers=headers)

    # Check if the request was successful and print client data
    if response.status_code == 200:
        return True
    else:
        return f'Error: {response.status_code} - {response.text}'

def get_client_data(session_id=get_session_id()):
    client_data=get_client(base_url=AWG_URL)
    result = f'Всего клиентов: {len(client_data)}\n'
    for client in client_data:
        # Convert transfer values from bytes to MBytes
        transfer_rx_mb = client['transferRx'] / (1024 ** 2) if client['transferRx'] else 0
        transfer_tx_mb = client['transferTx'] / (1024 ** 2) if client['transferTx'] else 0

        # Convert latestHandshakeAt to the desired format
        latest_handshake = datetime.strptime(client['latestHandshakeAt'], "%Y-%m-%dT%H:%M:%S.%fZ") if client['latestHandshakeAt'] else 'N/A'

        result += f"<strong>Name:</strong> {client['name']}\n"
        result += f"Address: `{client['address']}`\n"
        result += f"<blockquote expandable><strong>Extended Information:</strong>\n"
        result += f"- ID: `{client['id']}`\n"
        result += f"- Enabled: `{client['enabled']}`\n"
        result += f"- Latest Handshake At: `{latest_handshake}`\n\n"
        result += f"<strong>Transfer Data:</strong>\n"
        result += f"- Transfer TX: `{transfer_tx_mb:.2f} MB`\n"
        result += f"- Transfer RX: `{transfer_rx_mb:.2f} MB`\n"
        result += f"- Created At: `{client['createdAt']}`\n"
        result += f"- Updated At: `{client['updatedAt']}`\n"
        result += f"- Expired At: `{client['expiredAt'] if client['expiredAt'] else 'N/A'}`</blockquote>"

    return result

def create_new_client(client_name, base_url=AWG_URL, session_id=get_session_id()):
    # Make third request with session ID in Cookie header and provide a name for the new client to be created
    path = base_url + '/api/wireguard/client'
    name = client_name
    headers = {'Content-Type': 'application/json', 'Cookie': f'connect.sid={session_id}'}
    data = '{"name":"'+name+'"}'
    response = requests.post(path, headers=headers, data=data)

    # Check if the request was successful and print new client data
    if response.status_code == 200:

        client_data = get_client()

        for client in client_data:
            if client.get("name") == name:
                client_id = client.get("id")
                break
        
        return {"filename" : f'{name}.conf', "file" : get_config(client_id)}
    else:
        return f'Error: {response.status_code} - {response.text}'

def get_config(client_id, base_url=AWG_URL, session_id=get_session_id()):
    # Make third request with session ID in Cookie header and provide a name for the new client to be created
    path = base_url + '/api/wireguard/client/' + client_id + '/configuration'
    headers = {'Content-Type': 'application/json', 'Cookie': f'connect.sid={session_id}'}
    response = requests.get(path, headers=headers)

    # Check if the request was successful and print new client data
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

def get_qr(client_id, base_url=AWG_URL, session_id=get_session_id()):
    # Make third request with session ID in Cookie header and provide a name for the new client to be created
    path = base_url + '/api/wireguard/client/' + client_id + '/qrcode.svg'
    headers = {'Content-Type': 'application/json', 'Cookie': f'connect.sid={session_id}'}
    response = requests.get(path, headers=headers)

    # Check if the request was successful and print new client data
    if response.status_code == 200:
        print(response.text)
    else:
        print(f'Error: {response.status_code} - {response.text}')