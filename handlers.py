import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from scripts import *
from bot import ALLOWED_USERNAMES, BACKUP_PATH

# Define states for conversation
CREATE_CLIENT_NAME = 1

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

import re

def check_peer_name(client_name):
    # Check max length of 15 characters
    if len(client_name) > 15:
        return "String exceeds max length of 15 characters."

    # Check if string contains spaces, /, or :
    if any(char in client_name for char in [' ', '/', ':']):
        return "String contains invalid characters (spaces, /, or :)."

    # Check if string is '.' or '..'
    if client_name in ['.', '..']:
        return "String cannot be '.' or '..'."

    # If no issues, return None (meaning it's valid)

    # Check if name isn't used
    client_data = get_client()
    for client in client_data:
        if client["name"] == client_name:
            return f'{client_name} is already used by another peer. Please choose another one.'
    return None

def choose_client(action: str):
    client_data = get_client()
    keyboard = []
    for client in client_data:
        if action == 'get_config' or action == 'delete_client' or (action == 'disable_client' and client["enabled"] == True) or (action == 'enable_client' and client["enabled"] == False):
            keyboard.append([InlineKeyboardButton(f'{client["name"]}/{client["address"]}', callback_data=f"option_{action}:{client['id']}")])
    return keyboard

def options():
    return [
        [InlineKeyboardButton("Peer list", callback_data="button_clients")],
        [InlineKeyboardButton("Create backup", callback_data="button_get_backup")],
        [InlineKeyboardButton("Create peer", callback_data="button_create_client"), InlineKeyboardButton("Delete peer", callback_data="button_delete_client")],
        [InlineKeyboardButton("Enable peer", callback_data="button_enable_client"), InlineKeyboardButton("Disable peer", callback_data="button_disable_client")],
        [InlineKeyboardButton("Get config", callback_data="button_get_config"), InlineKeyboardButton("Get QR", callback_data="button_get_qr")],
    ]

# Получить текущих клиентов
async def handler_get_clients(update: Update, context: CallbackContext):
    return get_client_data()

# Создать клиента
async def handler_create_client(update: Update, context: CallbackContext):
    client_name = update.message.text
    logger.info(f"Client name received: {client_name}")

    nameCheck = check_peer_name(client_name)

    if nameCheck:
        await update.message.reply_text(nameCheck + "\n\nType a name for new peer. It must meet the conditions:\n\n - Max length of 15 characters\n - No Spaces, / or :\n Must not be . or ..\n - Must not be already used")
        return CREATE_CLIENT_NAME

    file_data = create_new_client(client_name)
    with open(file_data["filename"], 'wb') as f:
        f.write(file_data["file"])

    # Send file to the user
    await update.message.reply_document(document=open(file_data["filename"], 'rb'), caption='Импортируй файл в AmneziaWG.', reply_markup=InlineKeyboardMarkup(options()))
    os.remove(file_data["filename"])
    return ConversationHandler.END

async def handler_disable_client(client_id, update: Update, context: CallbackContext):
    if disable_client(client_id):
        return f'Client {client_id} has been disabled.'
    else:
        return f'Something went wrong while trying disable client {client_id}'

async def handler_delete_client(client_id, update: Update, context: CallbackContext):
    if delete_client(client_id):
        return f'Client {client_id} has been deleted.'
    else:
        return f'Something went wrong while trying delete client {client_id}'

async def handler_enable_client(client_id, update: Update, context: CallbackContext):
    if enable_client(client_id):
        return f'Client {client_id} has been enabled.'
    else:
        return f'Something went wrong while trying enable client {client_id}'

async def handler_get_config(client_id, update: Update, context: CallbackContext):
    query = update.callback_query
    callback_data = query.data  # This will be the callback_data you set on the buttons
    await query.answer()  # Acknowledge the button press
    
    client_data = get_client()

    for client in client_data:
        if client.get("id") == client_id:
            client_name = client.get("name")
            break

    file_data = get_config(client_id)
    with open(f'{client_name}.conf', 'wb') as f:
        f.write(file_data)

    params = {
        'document': open(f'{client_name}.conf', 'rb'),
        'reply_markup': InlineKeyboardMarkup(options()),
        'caption': 'Импортируй файл в AmneziaWG.'
    }

    params['chat_id'] = query.message.chat.id
    if query.message.message_thread_id:
        params['message_thread_id'] = query.message.message_thread_id
    await context.bot.send_document(**params)
    await query.message.delete()

    os.remove(f'{client_name}.conf')

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
        params['text'] = 'Replying to reqest...'


    if keyboard:
        params['reply_markup'] = InlineKeyboardMarkup(keyboard)

    if query.message and query.message.text:
        await query.edit_message_text(**params)
    else:
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
    # chat_id = query.message.chat.id
    # message_thread_id = query.message.message_thread_id
    
    # Handle button actions based on the callback data
    if callback_data == "button_clients":
        text = await handler_get_clients(update, context)
        keyboard = options()
        await handler_reply(text, keyboard, update, context)
    elif callback_data == "button_create_client":
        text = "Type a name for new peer. It must meet the conditions:\n\n - Max length of 15 characters\n - No Spaces, / or :\n - Must not be . or ..\n - Must not be already used"
        keyboard = None
        await handler_reply(text, keyboard, update, context)
        # await context.bot.send_message(text="Type a name for new peer...")
        return CREATE_CLIENT_NAME
    elif callback_data == "button_disable_client":
        if choose_client('disable_client'):
            text = "Choose peer to disble..."
            keyboard = choose_client('disable_client')
            await handler_reply(text, keyboard, update, context)
        else:
            text = "No peers available for disabling."
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
    elif callback_data == "button_delete_client":
        if choose_client('delete_client'):
            text = "Choose peer to delete..."
            keyboard = choose_client('delete_client')
            await handler_reply(text, keyboard, update, context)
        else:
            text = "No peers available for deleting."
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
    elif callback_data == "button_enable_client":
        if choose_client('enable_client'):
            text = "Choose peer to enable..."
            keyboard = choose_client('enable_client')
            await handler_reply(text, keyboard, update, context)
        else:
            text = "No peers available for enabling."
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
    elif callback_data == "button_get_config":
        if choose_client('get_config'):
            text = "Choose peer to download config..."
            keyboard = choose_client('get_config')
            await handler_reply(text, keyboard, update, context)
        else:
            text = "No peers available."
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
    elif callback_data == "button_get_backup":
        await handler_get_backup(update, context)
    elif callback_data.startswith("option_"):
        logger.info(f'Catch option_. Proceeding...')

        action, client_id = callback_data.split(":")  # client_id is after the colon
        
        if action == 'option_disable_client':
            logger.info(f'Catch {action}. Proceeding...')
            text = await handler_disable_client(client_id, update, context)
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
        elif action == 'option_enable_client':
            logger.info(f'Catch {action}. Proceeding...')
            text = await handler_enable_client(client_id, update, context)
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
        elif action == 'option_delete_client':
            logger.info(f'Catch {action}. Proceeding...')
            text = await handler_delete_client(client_id, update, context)
            keyboard = options()
            await handler_reply(text, keyboard, update, context)
        elif action == 'option_get_config':
            logger.info(f'Catch {action}. Proceeding...')
            text = await handler_get_config(client_id, update, context)
            keyboard = options()
            await handler_reply(text, keyboard, update, context)