from handlers import *  # Import all handler functions

# Define async function to handle the /start command
async def start(update: Update, context: CallbackContext):
    if not await check_username(update, context):
        return  # Stop further processing if the user is not authorized

    # Define inline keyboard for the response
    reply_markup = InlineKeyboardMarkup(options())
    
    # Send a message with inline buttons
    await update.message.reply_text("Choose options:", reply_markup=reply_markup)
    logger.info("Start command executed successfully.")

# Main function to start the bot
def main():
    logger.info("Starting the bot...")

    # Initialize the bot application with the token from environment variables
    application = Application.builder().token(BOT_TOKEN).build()

    # Set up a conversation handler with callback query handler
    conv_callback_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(callBackHandler)],
        states={
            CREATE_PEER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handler_create_peer)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Add conversation handler to the application
    application.add_handler(conv_callback_handler)

    # Start command handler
    application.add_handler(CommandHandler("start", start))
    
    # Start the bot by polling for updates
    logger.info("Bot is now polling for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# Ensure the event loop runs when starting the bot
if __name__ == '__main__':
    main()