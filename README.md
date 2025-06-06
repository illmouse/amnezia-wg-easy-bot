# amnezia-wg-easy-bot
Amnezia Wireguard telegram bot built with python telegram.ext

# What it can do

* List all peers
* Create/remove peer
* Enable/disable peer
* Get server backup
* Get peer config file
* Get peer config QR (not yet implemented)

# Screenshots

![Main menu](screenshots/main_menu.jpg)
![Peer list](screenshots/peer_list.jpg)
![Peer config](screenshots/new_peer_config.jpg)


# Set up bot

### Prerequisites

* Bot should have access to amnezia wg easy web interface
* Docker should be installed on host

### Example .env config:

``` bash
BOT_TOKEN=xxxxxxx # telegram bot token
ALLOWED_USERNAMES=username1,username2 # list of telegram usernames of users who should be able to use bot
AWG_URL=http://my.awgeasy.endpoint.lv:53821 # endpoint where amnezia wg easey web interface (API) is reachable
AWG_PASSWORD=myfavouritepassword # password for amnezia wg easey web
BACKUP_PATH=/opt/app # path to save backup file incide container
```

### Run

``` bash
# clone repository
git clone https://github.com/illmouse/amnezia-wg-easy-bot.git

# configure .env file
nano .env

# run bot
docker compose up -d
```

### Diagnose
``` bash
docker compose logs -f
```