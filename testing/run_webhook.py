#!/usr/bin/env python3
"""
This script runs the Telegram bot using the webhook method locally.
Useful for testing webhook functionality before deploying to a server.
Note: You'll need a tool like ngrok to expose your local server to the internet.
"""

import os
from dotenv import load_dotenv
from webhook_method.webhook_bot import start_webhook, set_webhook

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Set the bot mode to webhook
    os.environ["BOT_MODE"] = "webhook"
    
    # Start the webhook server
    print("Starting webhook server locally...")
    print("Note: To test webhooks locally, you need to expose your server to the internet.")
    print("You can use tools like ngrok (https://ngrok.com/) for this purpose.")
    
    # Start the webhook server
    start_webhook(host='0.0.0.0', port=5000, debug=True)
