from config.app_config import setup_logging, logger
from polling_method.polling_bot import start_polling
from webhook_method.webhook_bot import start_webhook
from config.app_config import BOT_MODE

# Initialize logger
setup_logging()

# Determine which mode to use (polling or webhook)
def get_bot_mode():
    
    mode = BOT_MODE
    if mode not in ['polling', 'webhook']:
        logger.warning(f"Invalid BOT_MODE: {mode}. Using webhook as default.")
        mode = "webhook"

    return mode

if __name__ == "__main__":
    mode = get_bot_mode()
    logger.info(f"Starting bot in {mode} mode")

    if mode == "polling":
        start_polling()
    else:
        # For local testing
        start_webhook(debug=True)
