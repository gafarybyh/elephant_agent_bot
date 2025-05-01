#!/usr/bin/env python3
"""
This script runs the Telegram bot using the polling method.
Use this for local development or when you don't have a public server for webhooks.
"""

import os
from dotenv import load_dotenv
from polling_method.polling_bot import start_polling

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Set the bot mode to polling
    os.environ["BOT_MODE"] = "polling"
    
    # Start the bot with polling
    print("Starting bot with polling method...")
    start_polling()
