import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from dotenv import load_dotenv
from handlers import *  # Import everything from handlers.py

# Load variables
BOT_TOKEN = os.environ.get("BOT_TOKEN", "botToken_123")
AWG_URL = os.environ.get("AWG_URL", 'http://wg.example.com:52820')
AWG_PASSWORD = os.environ.get("AWG_PASSWORD", "password")
ALLOWED_USERNAMES = os.environ.get('ALLOWED_USERNAMES', '@nouser').split(',')
BACKUP_PATH = os.environ.get("BACKUP_PATH", "/opt/app")
# BACKUP_INTERVAL_MIN = int(os.environ.get("BACKUP_INTERVAL_MIN", 30))

# Function to start command
async def start(update: Update, context: CallbackContext):
    # Check if the username is allowed
    if not await check_username(update, context):
        return  # Stop further processing if the user is not allowed
        
    # Define reply markup with inline keyboard
    reply_markup = InlineKeyboardMarkup(options())
    
    # Send the message with inline buttons
    await update.message.reply_text("Choose options:", reply_markup=reply_markup)
    logger.info("Start command executed successfully.")

# Main function to start the bot
def main():
    logger.info("Starting the bot...")

    # Use the bot token from the environment
    application = Application.builder().token(BOT_TOKEN).build()

    conv_callback_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(callBackHandler)],
        states={
            CREATE_CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handler_create_client)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_callback_handler)
    
    # Start command handler
    application.add_handler(CommandHandler("start", start))

    # Start polling for updates
    logger.info("Bot is now polling for updates...")

    # Start polling for updates
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# Ensure the event loop is running when starting the bot
if __name__ == '__main__':
    main()