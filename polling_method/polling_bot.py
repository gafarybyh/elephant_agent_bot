import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from analysis.macro import analyze_macro_news
from analysis.sector import analyze_sector
from helpers.api_helpers import save_id_to_google_sheets
from config.app_config import (
    logger, TELEGRAM_BOT_TOKEN, MINI_APP_URL, WELCOME_IMAGE_PATH,
    WELCOME_MESSAGE, HELP_MESSAGE, TOKEN_MESSAGE, INFO_MESSAGE,
    CONTACT_MESSAGE, MACRO_MESSAGE
)

# Initialize bot application
bot = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Command handlers
async def start(update: Update, context: CallbackContext):
    logger.info(f"User {update.effective_user.id} started the bot")

    keyboard = [
        [InlineKeyboardButton(
            "Open Screener",
            web_app={"url": MINI_APP_URL}
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        with open(WELCOME_IMAGE_PATH, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=WELCOME_MESSAGE,
                reply_markup=reply_markup
            )

            # Save user ID after welcome start
            chat_id = update.message.chat_id
            username = update.message.chat.username
            save_id_to_google_sheets(chat_id, username)

    except FileNotFoundError:
        logger.error(f"Welcome image not found at {WELCOME_IMAGE_PATH}")
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=reply_markup
        )

async def handle_analyze(update: Update, context: CallbackContext):
    user_message = update.message.text.strip()
    try:
        if "/sector" in user_message:
            await update.message.reply_text("Analyzing...")

            # Remove the "/sector" prefix from the user message
            clean_query = user_message.replace("/sector", "", 1).strip()

            analysis_result = analyze_sector(clean_query)
            
            await update.message.reply_text(analysis_result)
        
        elif "/macro" in user_message:
            await update.message.reply_text("Analyzing...")
            
            # Remove the "/macro" prefix from the user message
            clean_query = user_message.replace("/macro", "", 1).strip()
            
            analysis_result = analyze_macro_news(clean_query)
            
            await update.message.reply_text(analysis_result)

    except Exception as e:
        logger.error(f"Error while handling message: {e}")
        await update.message.reply_text("Error occurred while processing request. Try again later.")

async def token(update: Update, context: CallbackContext):
    logger.info(f"User {update.effective_user.id} requested token info")
    await update.message.reply_text(TOKEN_MESSAGE)

async def help(update: Update, context: CallbackContext):
    logger.info(f"User {update.effective_user.id} requested help")
    await update.message.reply_text(HELP_MESSAGE)

async def contact(update: Update, context: CallbackContext):
    logger.info(f"User {update.effective_user.id} requested contact info")
    await update.message.reply_text(CONTACT_MESSAGE)

async def info(update: Update, context: CallbackContext):
    logger.info(f"User {update.effective_user.id} requested info")
    await update.message.reply_text(INFO_MESSAGE)
    
async def macro(update: Update, context: CallbackContext):
    logger.info(f"User {update.effective_user.id} requested macro")
    await update.message.reply_text(MACRO_MESSAGE)

def setup_handlers():
    # Add handlers to the application
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("sector", handle_analyze))
    bot.add_handler(CommandHandler("token", token))
    bot.add_handler(CommandHandler("help", help))
    bot.add_handler(CommandHandler("info", info))
    bot.add_handler(CommandHandler("contact", contact))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_analyze))

async def run_polling():
    """Run the bot with polling method"""
    logger.info("Starting bot with polling method...")
    
    # Initialize the bot
    await bot.initialize()
    
    # Start polling
    await bot.start_polling()
    
    # Run the bot until the user presses Ctrl-C
    await bot.idle()

def start_polling():
    """Start the bot with polling method"""
    setup_handlers()
    try:
        asyncio.run(run_polling())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
    except Exception as e:
        logger.error(f"Error running bot: {e}")

if __name__ == "__main__":
    start_polling()
