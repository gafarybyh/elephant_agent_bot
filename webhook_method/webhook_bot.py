import requests
import asyncio
import json
from flask import Flask, request, Response
from analysis.sector import analyze_sector
from analysis.macro import analyze_macro_news
from analysis.token import format_category_tokens
from helpers.api_helpers import (
    broadcast_message_tg, get_all_chat_ids_from_sheets, save_id_to_google_sheets, reply_message_tg, delete_message_tg
)
from config.app_config import (
    logger, TELEGRAM_BOT_TOKEN, WEBHOOK_URL,
    WELCOME_MESSAGE, HELP_MESSAGE, TOKEN_MESSAGE, INFO_MESSAGE,
    CONTACT_MESSAGE
)

# Create Flask app
app = Flask(__name__)


# *WEBHOOK ROUTE
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Get the update from Telegram
        update_json = request.get_json(force=True)
        logger.info(f"Received update: {update_json}")

        # Extract basic information from the update
        if 'message' in update_json:

            # Get the chat ID and Username
            chat_id = update_json['message']['chat']['id']
            username = update_json['message']['chat'].get('username', '')

            # If it's a text message
            if 'text' in update_json['message']:
                text = update_json['message']['text']
                logger.info(f"Received message from {chat_id}: {text}")


                # Handle commands
                # TODO* START COMMAND
                if text.startswith('/start'):
                    reply_text = WELCOME_MESSAGE
 
                    reply_message_tg(chat_id, reply_text)

                    # Save user ID to Google Sheets when using webhook
                    try:
                        save_id_to_google_sheets(chat_id, username)
                    except Exception as e:
                        logger.error(f"Error saving user ID to Google Sheets: {e}")
                # *HELP COMMAND
                elif text.startswith('/help'):
                    reply_text = HELP_MESSAGE
                    reply_message_tg(chat_id, reply_text)

                    # Save user ID to Google Sheets when using webhook
                    try:
                        save_id_to_google_sheets(chat_id, username)
                    except Exception as e:
                        logger.error(f"Error saving user ID to Google Sheets: {e}")
                # *INFO COMMAND
                elif text.startswith('/info'):
                    reply_text = INFO_MESSAGE
                    reply_message_tg(chat_id, reply_text)
                # *CONTACT COMMAND
                elif text.startswith('/contact'):
                    reply_text = CONTACT_MESSAGE
                    reply_message_tg(chat_id, reply_text)
                # *TOKEN COMMAND
                elif text.startswith('/token'):
                    reply_text = TOKEN_MESSAGE
                    reply_message_tg(chat_id, reply_text)
                
                # TODO* LARGECAP COMMAND
                elif text.startswith('/largecap'):
                  
                    # Then generate momentum report
                    momentum_report = format_category_tokens("largeCap")

                    # Reply the analysis result
                    reply_message_tg(chat_id, momentum_report)
                
                # TODO* MIDCAP COMMAND
                elif text.startswith('/midcap'):
                    
                    # generate momentum report
                    momentum_report = format_category_tokens("midCap")

                    # Reply the analysis result
                    reply_message_tg(chat_id, momentum_report)
                
                # TODO* SMALLCAP COMMAND
                elif text.startswith('/smallcap'):
                
                    # generate momentum report
                    momentum_report = format_category_tokens("smallCap")

                    # Reply the analysis result
                    reply_message_tg(chat_id, momentum_report)
                
                # TODO* MICROCAP COMMAND
                elif text.startswith('/microcap'):
                    
                    # Then generate momentum report
                    momentum_report = format_category_tokens("microCap")

                    # Reply the analysis result
                    reply_message_tg(chat_id, momentum_report)

                # TODO* SECTOR COMMAND
                elif text.startswith('/sector'):
                    reply_text = "Analyzing sector data...please wait"
                    # Send initial response and return message_id
                    msg_id = reply_message_tg(chat_id, reply_text)

                    # Remove the "/sector" prefix from the user message
                    clean_query_sector = text.replace("/sector", "", 1).strip()

                    # Then analyze sector
                    sector_analysis_result = analyze_sector(clean_query_sector)
                    
                    if msg_id is not None:
                        # Delete the initial response
                        delete_message_tg(chat_id, msg_id)

                    # Reply the analysis result
                    reply_message_tg(chat_id, sector_analysis_result)


                # TODO* MACRO COMMAND
                elif text.startswith('/macro'):
                    reply_text = "Analyzing news sources… please wait"
                    # Send initial response and return message_id
                    msg_id = reply_message_tg(chat_id, reply_text)

                    # Remove the "/macro" prefix from the user message
                    clean_query_macro = text.replace("/macro", "", 1).strip()

                    # Then analyze Macro News
                    macro_analysis_result = analyze_macro_news(clean_query_macro)

                    if msg_id is not None:
                        # Delete the initial response
                        delete_message_tg(chat_id, msg_id)

                    # Reply the analysis result
                    reply_message_tg(chat_id, macro_analysis_result)
                

        logger.info("Telegram message sent successfully")
        return Response('OK', status=200)
    except Exception as e:
        logger.error(f"Error processing update webhook: {e}")
        return Response('OK', status=200)  # Still return 200 to avoid Telegram retries

# TODO* SET WEBHOOK
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    try:
        # Make a direct API call to set the webhook
        token = TELEGRAM_BOT_TOKEN
        api_url = f"https://api.telegram.org/bot{token}/setWebhook"
        params = {
            "url": WEBHOOK_URL,
            "drop_pending_updates": True,
            "allowed_updates": ["message", "callback_query"]
        }

        response = requests.post(api_url, json=params)
        result = response.json()

        if result.get("ok"):
            logger.info(f"Webhook set to {WEBHOOK_URL}")
            return f"Webhook successfully set to {WEBHOOK_URL}. Response: {result}"
        else:
            logger.error(f"Failed to set webhook: {result}")
            return f"Failed to set webhook: {result}", 500
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return f"Error setting webhook: {e}", 500

# TODO* TRIGGER MACRO NOTIFICATION
@app.route('/trigger_macro', methods=['POST'])
def trigger_macro_notification():
    try:
        # Try to parse JSON with explicit error handling
        try:
            data = request.get_json(force=True)
        except json.JSONDecodeError as json_err:
            logger.error(f"Invalid JSON in request: {json_err}")
            return Response(f"Invalid JSON format: {str(json_err)}", status=400)

        if not data or data.get("key") != "macro":
            return Response("Unauthorized", status=403)
        
        macro_analysis_result = analyze_macro_news()
        
        all_chat_ids = get_all_chat_ids_from_sheets()
        if not all_chat_ids:
            logger.warning("No chat IDs found to broadcast to")
            return Response("No recipients found", status=200)
        
        broadcast_message_tg(all_chat_ids, macro_analysis_result)
        
        logger.info("Macro analysis broadcasted successfully")
        return Response('OK', status=200)
    except Exception as e:
        logger.error(f"Error in trigger_macro_notification: {e}")
        return Response(f"Error processing macro notification: {str(e)}", status=500)        


# TODO* START WEBHOOK
def start_webhook(host='0.0.0.0', port=5000, debug=False):
    """Start the Flask app for webhook"""
    logger.info(f"Starting webhook server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    # For development
    start_webhook(debug=False)



