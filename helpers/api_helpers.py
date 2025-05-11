import requests
import json
import os
from datetime import datetime
import time
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from helpers.utils import split_text
from config.app_config import (PROJECT_ROOT, logger, RSS2JSON_API_KEY, SHEET_URL_ID, GEMINI_API_KEY, GOOGLE_CREDENTIALS, TELEGRAM_BOT_TOKEN)


# TODO* FETCH DATA SECTOR
def fetch_data_sector():
    url = f"https://raynor-api.gafarybyh.workers.dev/sheets/{SHEET_URL_ID}/Sector%20Category"
    try:
        response = requests.get(url) 
        response.raise_for_status()  # Memastikan status OK (200)

        # Periksa apakah response JSON yang diterima sesuai format yang diharapkan
        try:
            sectors = response.json()
            # Bisa tambahkan pengecekan apakah key 'values' ada di dalam data
            if 'values' not in sectors:
                raise ValueError("Missing 'values' in the SECTOR response data")

            return sectors
        except ValueError as ve:
            logger.error(f"Invalid JSON or missing expected key in SECTOR response: {ve}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from API Sector: {e}")
        return None

# TODO* FETCH DATA TOKEN
def fetch_data_token():
    url = f"https://raynor-api.gafarybyh.workers.dev/sheets/{SHEET_URL_ID}/Tokens"
    try:
        response = requests.get(url)
        response.raise_for_status()
        try:
            tokens = response.json()

            if 'values' not in tokens:
                raise ValueError("Missing 'values' in the TOKEN response data")

            return tokens
        except ValueError as ve:
            logger.error(f"Invalid JSON or missing expected key in TOKEN response: {ve}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from API Token: {e}")
        return None

# TODO* FETCH CALENDAR ECONOMY
def fetch_calendar_economy():
    url = "https://raynor-api.gafarybyh.workers.dev/calendar"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Akan raise error kalau status bukan 200 OK

        calendar_data = response.json()  # Parse JSON dari respons
        return calendar_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error: Failed to fetch data from Calendar Economy: {e}")
        return None
    except ValueError as e:
        logger.error(f"Error: Failed to parse JSON: {e}")
        return None

# TODO* FETCH FINANCIALJUICE FEED
def fetch_financialjuice_feed(limit: int = 50):
    # URL untuk mendapatkan feed dari RSS2JSON API
    url = 'https://api.rss2json.com/v1/api.json'
    params = {
        'rss_url': 'https://www.financialjuice.com/feed.ashx?xy=rss',
        'api_key': RSS2JSON_API_KEY,  # Ganti dengan API key kamu jika perlu
        'order_by': 'pubDate',  # Mengurutkan berdasarkan waktu publikasi
        'order_dir': 'desc',  # Urutan descending
        'count': limit  # Ambil 50 berita terbaru
    }

    try:
        # Mengambil data dari API
        response = requests.get(url, params=params)
        response.raise_for_status()  # Mengecek apakah ada error HTTP (misalnya 404, 500)

        # Mengambil data JSON dari response
        feed = response.json()

        # Memastikan data valid
        if feed.get('status') != 'ok':
            logger.error(f"FinancialJuice API status returned an error: {feed.get('message', 'Unknown error')}")
            return None

        return feed
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from FinancialJuice: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while processing FinancialJuice feed: {e}")
        return None

# TODO* REPLY MESSAGE TELEGRAM
def reply_message_tg(chat_id: int, text: str):
    """
    Bot reply telegram message

    Args:
        chat_id (int): Chat ID to send message
        text (str): Message to send
    Returns:
        message_id (int): Message ID of the first chunk or None if error

    """
    if text is None:
        logger.error("Cannot send None as message text")
        return None

    # Convert to string if not already
    if not isinstance(text, str):
        text = str(text)

    token = TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # if text is too long, split it
    text_chunks = split_text(text)

    first_message_id = None

    try:
        for i, chunk in enumerate(text_chunks):
            request = requests.post(url, json={
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "Markdown"
            })
            response = request.json()

            # Check if the response contains the expected keys
            if response.get('ok') and 'result' in response and 'message_id' in response['result']:
                message_id = response['result']['message_id']

                # Save the first message ID to return
                if i == 0:
                    first_message_id = message_id
            else:
                logger.error(f"Unexpected response format from Telegram API: {response}")

        return first_message_id

    except Exception as e:
        logger.error(f"Error while POST a telegram message: {e}")
        return None


# TODO* BROADCAST MESSAGE
def broadcast_message_tg(chat_ids: list, text: str):
    for chat_id in chat_ids:
        message_id = reply_message_tg(chat_id, text)
        if message_id:
            logger.info(f"Message sent to {chat_id}")
        else:
            logger.warning(f"Failed send message to {chat_id}")
        
        time.sleep(0.5)  # delay untuk hindari rate limit Telegram


# TODO* DELETE MESSAGE TELEGRAM
def delete_message_tg(chat_id: int, message_id: int):
    token = TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/deleteMessage"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
    }
    try:
        response_data = requests.post(url, json=data)
        return response_data.json()
    except Exception as e:
        logger.error(f"Error while DELETE a telegram message: {e}")

# TODO* FETCH GEMINI API
def get_gemini_response(prompt):
    """
    Get response from Gemini API

    Args:
        prompt (str): Prompt to send to Gemini API
    Returns:
        str: Response from Gemini API or error message
    """
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)

        # Check if response has text attribute
        if hasattr(response, 'text'):
            return response.text.strip()
        else:
            logger.error(f"Unexpected response format from Gemini API: {response}")
            return "Failed to get a valid response from AI, try again later..."

    except Exception as e:
        logger.error(f"Error occurred while fetching Gemini API: {e}")
        return "Failed while processing AI response, try again later..."

# TODO* FETCH GEMINI API
def get_gemini_response_v2(prompt):
    """
    Get response from Gemini API

    Args:
        prompt (str): Prompt to send to Gemini API
    Returns:
        str: Response from Gemini API or error message
    """
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    
        model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
        response = model.generate_content(prompt)

        # Check if response has text attribute
        if hasattr(response, 'text'):
            return response.text.strip()
        else:
            logger.error(f"Unexpected response format from Gemini API: {response}")
            return "Failed to get a valid response from AI, try again later..."

    except Exception as e:
        logger.error(f"Error occurred while fetching Gemini API: {e}")
        return "Failed while processing AI response, try again later..."


# TODO* GOOGLE SHEET API CONFIG
def setup_google_sheets():

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Path ke credentials.json di root project
    project_root = PROJECT_ROOT
    creds_path = os.path.join(project_root, "credentials.json")
    
    # Coba gunakan file credentials.json terlebih dahulu
    if os.path.exists(creds_path):
        try:
            logger.info(f"Menggunakan credentials dari file: {creds_path}")
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            client = gspread.authorize(creds)
            return client
        except Exception as e:
            logger.warning(f"Error menggunakan credentials dari file: {e}")
            logger.info("Mencoba fallback ke environment variable...")
            # Lanjut ke fallback
    else:
        logger.warning(f"File credentials tidak ditemukan di: {creds_path}")
        logger.info("Mencoba fallback ke environment variable...")
        # Lanjut ke fallback
    
    # Fallback: Coba gunakan credentials dari environment variable
    try:
        google_creds_json = GOOGLE_CREDENTIALS
        if not google_creds_json:
            logger.error("Environment variable GOOGLE_CREDENTIALS kosong")
            raise ValueError("GOOGLE_CREDENTIALS kosong")
            
        logger.info("Menggunakan credentials dari environment variable")
        
        # Coba perbaiki format JSON yang umum bermasalah
        fixed_json = google_creds_json.replace('\\"', '"').replace('\\n', '\n')
        
        try:
            # Coba parse JSON
            creds_dict = json.loads(fixed_json)
        except json.JSONDecodeError as e:
            logger.error(f"JSON tidak valid: {e}")
            raise
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        logger.error(f"Error menggunakan credentials dari environment variable: {e}")
        raise Exception(f"Tidak dapat mengautentikasi ke Google Sheets: {e}")

# TODO* SAVE TELEGRAM ID TO GOOGLE SHEET
def save_id_to_google_sheets(chat_id, username):
    try:
        client = setup_google_sheets()

        # Open sheet 'CoinData' then select worksheet
        sheet = client.open("CoinData").worksheet("Elephant Agent User")

        # Tambahkan header (opsional) jika belum ada
        if sheet.cell(1, 1).value is None:  # Jika sel A1 kosong
            sheet.update("A1", [["Chat ID", "Username", "Timestamp"]])

        # Periksa apakah Chat ID sudah ada
        chat_ids = sheet.col_values(1)  # Ambil semua Chat ID dari kolom A
        if str(chat_id) in chat_ids:
            # print(f"Chat ID {chat_id} sudah terdaftar. Tidak menambahkan.")
            return
        
        logger.info(f"Saving user {chat_id} with username {username} to Google Sheets")
        
        # Menambahkan data ke baris berikutnya mulai dari baris kedua
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([chat_id, username, timestamp])
        
        logger.info(f"Successfully saved user {chat_id} to Google Sheets")
    except Exception as e:
        logger.error(f"Error saving user ID to Google Sheets: {e}")
        # Continue execution without raising the exception

# TODO* GET ALL CHAT IDs FROM GOOGLE SHEET
def get_all_chat_ids_from_sheets():
    try:
        client = setup_google_sheets()
        sheet = client.open("CoinData").worksheet("Elephant Agent User")

        chat_ids = sheet.col_values(1)[1:]  # skip header
        valid_chat_ids = []

        for cid in chat_ids:
            try:
                cid_int = int(cid)
                valid_chat_ids.append(cid_int)
            except ValueError:
                logger.warning(f"Invalid chat ID found: {cid}")

        logger.info(f"Retrieved {len(valid_chat_ids)} valid chat IDs from sheets")
        return valid_chat_ids
    except Exception as e:
        logger.error(f"Error retrieving chat IDs from sheets: {e}")
        return []  # Return empty list instead of None on error
