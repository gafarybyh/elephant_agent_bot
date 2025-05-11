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

# Project Root PythonAnywhere
PROJECT_ROOT = "/home/gafarybyh/elephant_agent_bot"

# Environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RSS2JSON_API_KEY = os.getenv("RSS2JSON_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')
SHEET_URL_ID = os.getenv("SHEET_URL_ID")
BOT_MODE = os.getenv("BOT_MODE", "webhook") # Default to webhook
X_USERNAME = os.getenv("X_USERNAME")
X_EMAIL = os.getenv("X_EMAIL")
X_PASSWORD = os.getenv("X_PASSWORD")

# Webhook Config for PythonAnywhere
WEBHOOK_USERNAME = "gafarybyh" 
WEBHOOK_URL = f"https://{WEBHOOK_USERNAME}.pythonanywhere.com/webhook"

# Telegram Config
MINI_APP_URL = "https://elephant-agent.pages.dev/"
WELCOME_IMAGE_PATH = 'raynor-bg.jpg'

WELCOME_MESSAGE = (
    "👋 Welcome to Elephant Agent Bot!\n\n"
    "Your AI-Powered Crypto Analysis Assistant, designed to help crypto traders make smarter decisions through comprehensive market analysis and AI-powered insights.\n\n"
    "🔍 Available Features:\n"
    "• Market Dominance Alert\n"
    "• Hype Tokens Alert\n"
    "• Crypto Screener\n"
    "• Macro Sentiment Analysis\n"
    "• Smart market insights powered by AI\n"
    "Click the button below to open Screener! or /help to see command"
)

HELP_MESSAGE = (
    "🤖 **Available Commands:**\n\n"
    "📌 **Basic Commands:**\n"
    "  /start - Start the bot\n"
    "  /help - Show all commands\n"
    "  /info - Get bot information\n"
    "  /contact - Contact support\n\n"
    "📊 **Analysis Commands:**\n"
    "  /sector - Ask AI to analyze a sector\n"
    "    _Example: /sector how is DeFi performing today?_\n"
    "  /macro - Ask AI to analyze current macro sentiment\n"
    "    _Example: /macro what is the crypto sentiment of today's news?_\n\n"
    "📈 **Market Momentum Scan (up to 15 tokens):**\n"
    "  /largecap - Show largecap momentum tokens\n"
    "  /midcap - Show midcap momentum tokens\n"
    "  /smallcap - Show smallcap momentum tokens\n"
    "  /microcap - Show microcap momentum tokens\n"
    "🚀 **Coming Soon:**\n"
    "  /token - Ask AI to analyze a specific token\n"
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

