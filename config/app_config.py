import os
import logging
from config.logging_config import logging_config
from dotenv import load_dotenv

# Load variabel dari file .env
load_dotenv() # Untuk baca local .env

# Configure logger
def setup_logging():
    logging.config.dictConfig(logging_config)

logger = logging.getLogger(__name__)

# Environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RSS2JSON_API_KEY = os.getenv("RSS2JSON_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')
SHEET_URL_ID = os.getenv("SHEET_URL_ID")

# Sheet URL
SHEET_URL_SECTOR = f"https://raynor-api.gafarybyh.workers.dev/sheets/{SHEET_URL_ID}/Sector%20Category"

SHEET_URL_TOKEN = f"https://raynor-api.gafarybyh.workers.dev/sheets/{SHEET_URL_ID}/Tokens"

# Webhook Config for PythonAnywhere
WEBHOOK_USERNAME = "gafarybyh" 
WEBHOOK_URL = f"https://{WEBHOOK_USERNAME}.pythonanywhere.com/webhook"

# Bot Mode
BOT_MODE = os.getenv("BOT_MODE", "webhook") # Default to webhook

# Telegram Config
MINI_APP_URL = "https://elephant-agent.pages.dev/"
WELCOME_IMAGE_PATH = 'raynor-bg.jpg'

WELCOME_MESSAGE = (
    "👋 Welcome to Elephant Agent Bot!\n\n"
    "Your AI-Powered Crypto Analysis Assistant\n\n"
    "🔍 Available Features:\n"
    "• Market Dominance Alert\n"
    "• Hype Tokens Alert\n"
    "• Crypto Screener\n"
    "• Macro Sentiment Analysis\n"
    "• AI Analysis (Under development)\n\n"
    "Click the button below to open Screener! or /help to see command"
)

HELP_MESSAGE = (
    "🤖 Available Commands:\n\n"
    "Basic Commands:\n"
    "/start - Start the bot\n"
    "/help - Show all commands\n"
    "/info - Bot information\n"
    "/contact - Contact support\n\n"
    "Analysis Commands:\n"
    "/sector - Ask AI to analyze sector\n"
    "Example: /sector how is defi performing today?\n\n"
    "/macro - Ask AI to analyze current Macro Sentiment\n"
    "Example: /macro what is the sentiment of today's news?\n\n"
    "Coming Soon:\n"
    "/token - Ask AI to analyze token"
)

TOKEN_MESSAGE = (
    "This feature is currently under development and will be available soon. Stay tuned!"
)

INFO_MESSAGE = (
    "🐘 About Elephant Agent Bot\n\n"
    "Your AI-Powered Crypto Analysis Assistant\n\n"
    "🎯 Purpose:\n"
    "Designed to help crypto traders make smarter decisions through comprehensive market analysis and AI-powered insights.\n\n"
    "💪 Key Features:\n"
    "• Hourly analysis and trends\n"
    "• Smart market insights powered by AI\n"
    "• Data-driven crypto screener\n"
    "• Market dominance tracking\n"
    "• Emerging token detection\n\n"
    "🎁 Value Proposition:\n"
    "Elephant Agent helps you stay updated with market analysis to enhance your trading decisions.\n\n"
    "🔒 Built with reliability and accuracy in mind."
)

CONTACT_MESSAGE = (
    "📞 Contact Information\n\n"
    "Need help or have suggestions?\n\n"
    "Developer: Gafa\n"
    "Email: gafarybyh@gmail.com\n"
    "Telegram: @gafarybyh\n\n"
    "We'll respond as soon as possible!"
)

MACRO_MESSAGE = (
    "This feature is currently under development and will be available soon. Stay tuned!"
)

