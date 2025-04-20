########### IMPORTS ###########
from telegram import Update, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from scripts import *

########### CONVERSATION STATES ###########
# Define states for conversation
CREATE_PEER_NAME = 1

# Constant variables
NEW_PEER_HOLDER = "\n\nType a name for new peer. It must meet the conditions:\n\n - Max length of 15 characters\n - No Spaces, / or :\n Must not be . or ..\n - Must not be already used"

########### HELPER FUNCTIONS ###########
# Function to check if the username is allowed
def is_allowed_user(username: str) -> bool:
    return username in ALLOWED_USERNAMES

# Common function to check if the username is allowed
async def check_username(update: Update, context: CallbackContext):
    # Get the username (it can be accessed via update.message.from_user.username or update.callback_query.from_user.username)
    if update.message:
        username = update.message.from_user.username
    elif update.callback_query:
        username = update.callback_query.from_user.username
    else:
        username = None

    # If the username is not allowed, stop further processing
    if username and not is_allowed_user(username):
        await update.message.reply_text("You are not authorized to use this bot.")
        return False  # Stop further processing of the update
    return True  # Username is allowed, continue with the logic

def check_peer_name(peer_name):
    # Check max length of 15 characters
    if len(peer_name) > 15:
        return "String exceeds max length of 15 characters."

    # Check if string contains spaces, /, or :
    if any(char in peer_name for char in [' ', '/', ':']):
        return "String contains invalid characters (spaces, /, or :)."

    # Check if string is '.' or '..'
    if peer_name in ['.', '..']:
        return "String cannot be '.' or '..'."

    # If no issues, return None (meaning it's valid)

    # Check if name isn't used
    peer_data = get_peers()
    for peer in peer_data:
        if peer["name"] == peer_name:
            return f'{peer_name} is already used by another peer. Please choose another one.'
    return None

def choose_peer(action: str):
    peer_data = get_peers()
    keyboard = []
    for peer in peer_data:
        if action == 'get_peer_config' or action == 'delete_peer' or (action == 'disable_peer' and peer["enabled"] == True) or (action == 'enable_peer' and peer["enabled"] == False):
            keyboard.append([InlineKeyboardButton(f'{peer["name"]}/{peer["address"]}', callback_data=f"option_{action}:{peer['id']}")])
    return keyboard

def options():
    return [
        [InlineKeyboardButton("Peer list", callback_data="button_peers")],
        [InlineKeyboardButton("Create backup", callback_data="button_get_backup")],
        [InlineKeyboardButton("Create peer", callback_data="button_create_peer"), InlineKeyboardButton("Delete peer", callback_data="button_delete_peer")],
        [InlineKeyboardButton("Enable peer", callback_data="button_enable_peer"), InlineKeyboardButton("Disable peer", callback_data="button_disable_peer")],
        [InlineKeyboardButton("Get config", callback_data="button_get_config"), InlineKeyboardButton("Restart", callback_data="button_restart")],
    ]

########### HANDLERS ###########

# Define async function to handle the /start command
async def start(update: Update, context: CallbackContext):
    if not await check_username(update, context):
        return  # Stop further processing if the user is not authorized

    text = "Choose options:"
    keyboard = options()

    # Define inline keyboard for the response
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send a message with inline buttons
    try:
        await update.message.reply_text(text, reply_markup=reply_markup)
    except:
        await handler_reply(text, keyboard, update, context)

    logger.info("Start command executed successfully.")

# Get formatted list of peers
async def handler_get_peers(update: Update, context: CallbackContext, page_number):
    peer_data = get_peers()
    pages = pages_count(peer_data, group_size=5)
    keyboard = [[InlineKeyboardButton("Return to main menu", callback_data=f"start")],[]]

    for i in range(pages):
        keyboard[1].append(InlineKeyboardButton(i+1, callback_data=f"button_peers:{i}"))

    result = {
        'text': extract_peer_data(peer_data, page_number),
        'keyboard' : keyboard
    }

    await update.callback_query.message.delete()

    return result

# Create peer
async def handler_create_peer(update: Update, context: CallbackContext):
    peer_name = update.message.text
    logger.info(f"Peer name received: {peer_name}")

    nameCheck = check_peer_name(peer_name)

    if nameCheck:
        await update.message.reply_text(nameCheck + NEW_PEER_HOLDER)
        return CREATE_PEER_NAME

    file_data = create_new_peer(peer_name)

    # Check if required keys exist and are valid
    if not file_data or "filename" not in file_data or "file" not in file_data:
        error_msg = f"Something went wrong while creating the peer.\nDetails: {file_data}"
        logger.error(error_msg)
        await update.message.reply_text(error_msg)
        return ConversationHandler.END
        
    with open(file_data["filename"], 'wb') as f:
        f.write(file_data["file"])

    # Send file to the user
    await update.message.reply_document(document=open(file_data["filename"], 'rb'), caption='Import file in AmneziaWG.\n<a href="https://play.google.com/store/apps/details?id=org.amnezia.awg&pcampaignid=web_share">Playstore</a> | <a href="https://apps.apple.com/ru/app/amneziawg/id6478942365">AppStore</a> | <a href="https://github.com/amnezia-vpn/amneziawg-windows-client/releases/tag/1.0.0">Windows</a>', reply_markup=InlineKeyboardMarkup(options()), parse_mode='HTML')
    os.remove(file_data["filename"])
    return ConversationHandler.END

async def handler_disable_peer(peer_id, update: Update, context: CallbackContext):
    if disable_peer(peer_id):
        return f'Peer {peer_id} has been disabled.'
    else:
        return f'Something went wrong while trying disable peer {peer_id}'

async def handler_delete_peer(peer_id, update: Update, context: CallbackContext):
    if delete_peer(peer_id):
        return f'Peer {peer_id} has been deleted.'
    else:
        return f'Something went wrong while trying delete peer {peer_id}'

async def handler_enable_peer(peer_id, update: Update, context: CallbackContext):
    if enable_peer(peer_id):
        return f'Peer {peer_id} has been enabled.'
    else:
        return f'Something went wrong while trying enable peer {peer_id}'

async def handler_get_config(peer_id, update: Update, context: CallbackContext):
    query = update.callback_query
    callback_data = query.data  # This will be the callback_data you set on the buttons
    await query.answer()  # Acknowledge the button press
    
    peer_data = get_peers()

    for peer in peer_data:
        if peer.get("id") == peer_id:
            peer_name = peer.get("name")
            break

    file_data = get_peer_config(peer_id)
    with open(f'{peer_name}.conf', 'wb') as f:
        f.write(file_data)

    params = {
        'document': open(f'{peer_name}.conf', 'rb'),
        'reply_markup': InlineKeyboardMarkup(options()),
        'parse_mode': 'HTML',
        'caption': 'Import file in AmneziaWG.\n<a href="https://play.google.com/store/apps/details?id=org.amnezia.awg&pcampaignid=web_share">Playstore</a> | <a href="https://apps.apple.com/ru/app/amneziawg/id6478942365">AppStore</a> | <a href="https://github.com/amnezia-vpn/amneziawg-windows-client/releases/tag/1.0.0">Windows</a>'
    }

    params['chat_id'] = query.message.chat.id
    if query.message.message_thread_id:
        params['message_thread_id'] = query.message.message_thread_id
    await context.bot.send_document(**params)
    await query.message.delete()

    os.remove(f'{peer_name}.conf')

async def handler_get_backup(update: Update, context: CallbackContext):
    query = update.callback_query
    callback_data = query.data  # This will be the callback_data you set on the buttons
    await query.answer()  # Acknowledge the button press
    
    backup_file_path = os.path.join(BACKUP_PATH, 'wg0.json')
    
    create_backup()

    params = {
        'document': open(backup_file_path, 'rb'),
        'reply_markup': InlineKeyboardMarkup(options())
    }

    params['chat_id'] = query.message.chat.id
    if query.message.message_thread_id:
        params['message_thread_id'] = query.message.message_thread_id
    await context.bot.send_document(**params)
    await query.message.delete()

async def handler_reply(text, keyboard, update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat.id
    message_thread_id = query.message.message_thread_id

    params = {
        'parse_mode': 'HTML'
    }

    if text:
        params['text'] = text
    else:
        params['text'] = 'Replying to request...'


    if keyboard:
        params['reply_markup'] = InlineKeyboardMarkup(keyboard)

    # if query.message and query.message.text:
    try:
        await query.edit_message_text(**params)
    except:
    # else:
        params['chat_id'] = chat_id
        if message_thread_id:
            params['message_thread_id'] = message_thread_id
        await context.bot.send_message(**params)

# Callback query handler to handle button presses
async def callBackHandler(update: Update, context: CallbackContext):
    # Check if the username is allowed
    if not await check_username(update, context):
        return  # Stop further processing if the user is not allowed
    
    query = update.callback_query
    logger.info(f'Button was {query.data} pressed')
    callback_data = query.data  # This will be the callback_data you set on the buttons
    await query.answer()  # Acknowledge the button press
    
    # Start from beggining
    if query.data == "start":
        await start(update, context)  # Call the start function again
    # Handle button actions based on the callback data
    if query.data == "button_restart":
        sys.exit(1)
    if callback_data.startswith("button_peers"):
        page_number = 0
        if ":" in callback_data:
            page_number = callback_data.split(":")[1]  # peer_id is after the colon
        peers_data = await handler_get_peers(update, context, page_number)
        # logger.info(f'Here is peers_data {peers_data}')
        await handler_reply(peers_data["text"], peers_data["keyboard"], update, context)
        # text = await handler_get_peers(update, context)
        # keyboard = options()
        # await handler_reply(text, keyboard, update, context)
    elif callback_data == "button_create_peer":
        text = NEW_PEER_HOLDER
        keyboard = None
        await handler_reply(text, keyboard, update, context)
        # await context.bot.send_message(text="Type a name for new peer...")
        return CREATE_PEER_NAME
    elif callback_data == "button_disable_peer":
        if choose_peer('disable_peer'):
            text = "Choose peer to disble..."
            keyboard = choose_peer('disable_peer')
            await handler_reply(text, keyboard, update, context)
        else:
            text = "No peers available for disabling."
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
    elif callback_data == "button_delete_peer":
        if choose_peer('delete_peer'):
            text = "Choose peer to delete..."
            keyboard = choose_peer('delete_peer')
            await handler_reply(text, keyboard, update, context)
        else:
            text = "No peers available for deleting."
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
    elif callback_data == "button_enable_peer":
        if choose_peer('enable_peer'):
            text = "Choose peer to enable..."
            keyboard = choose_peer('enable_peer')
            await handler_reply(text, keyboard, update, context)
        else:
            text = "No peers available for enabling."
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
    elif callback_data == "button_get_config":
        if choose_peer('get_peer_config'):
            text = "Choose peer to download config..."
            keyboard = choose_peer('get_peer_config')
            await handler_reply(text, keyboard, update, context)
        else:
            text = "No peers available."
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
    elif callback_data == "button_get_backup":
        await handler_get_backup(update, context)
    elif callback_data.startswith("option_"):
        logger.info(f'Catch option_. Proceeding...')

        action, peer_id = callback_data.split(":")  # peer_id is after the colon
        
        if action == 'option_disable_peer':
            logger.info(f'Catch {action}. Proceeding...')
            text = await handler_disable_peer(peer_id, update, context)
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
        elif action == 'option_enable_peer':
            logger.info(f'Catch {action}. Proceeding...')
            text = await handler_enable_peer(peer_id, update, context)
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
        elif action == 'option_delete_peer':
            logger.info(f'Catch {action}. Proceeding...')
            text = await handler_delete_peer(peer_id, update, context)
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
        elif action == 'option_get_peer_config':
            logger.info(f'Catch {action}. Proceeding...')
            text = await handler_get_config(peer_id, update, context)