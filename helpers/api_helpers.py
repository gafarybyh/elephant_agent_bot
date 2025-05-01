import requests
import json
from datetime import datetime
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config.app_config import (logger, RSS2JSON_API_KEY, SHEET_URL_SECTOR, SHEET_URL_TOKEN, GEMINI_API_KEY, GOOGLE_CREDENTIALS)


# TODO* FETCH DATA SECTOR
def fetch_data_sector():
    try:
        response = requests.get(SHEET_URL_SECTOR)
        response.raise_for_status()  # Memastikan status OK (200)
        
        # Periksa apakah response JSON yang diterima sesuai format yang diharapkan
        try:
            data = response.json()
            # Bisa tambahkan pengecekan apakah key 'values' ada di dalam data
            if 'values' not in data:
                raise ValueError("Missing 'values' in the response data")
            
            return data
        except ValueError as ve:
            logger.error(f"Invalid JSON or missing expected key in response: {ve}")
            return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from API Sector: {e}")
        return None

# TODO* FETCH DATA TOKEN
def fetch_data_token():

    try:
        response = requests.get(SHEET_URL_TOKEN)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from API Token: {e}")
        return "Failed to fetch data from API Token"
    
# TODO* FETCH FINANCIALJUICE FEED
def fetch_financialjuice_feed():
    # URL untuk mendapatkan feed dari RSS2JSON API
    url = 'https://api.rss2json.com/v1/api.json'
    params = {
        'rss_url': 'https://www.financialjuice.com/feed.ashx?xy=rss',
        'api_key': RSS2JSON_API_KEY,  # Ganti dengan API key kamu jika perlu
        'order_by': 'pubDate',  # Mengurutkan berdasarkan waktu publikasi
        'order_dir': 'desc',  # Urutan descending
        'count': 30  # Ambil 30 berita terbaru
    }

    try:
        # Mengambil data dari API
        response = requests.get(url, params=params)
        response.raise_for_status()  # Mengecek apakah ada error HTTP (misalnya 404, 500)

        # Mengambil data JSON dari response
        data = response.json()

        # Memastikan data valid
        if data.get('status') != 'ok':
            logger.error(f"FinancialJuice API status returned an error: {data.get('message', 'Unknown error')}")
            return None

        # Ambil daftar berita dari JSON
        all_feed = []
        for item in data.get('items', []):
            all_feed.append({
                'title': item.get('title'),
                'published': item.get('pubDate')
            })
        
        return all_feed

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from FinancialJuice: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while processing FinancialJuice feed: {e}")
        return None


# TODO* FETCH GEMINI API
def get_gemini_response(prompt):

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error occurred while fetching Gemini API: {e}")
        return "Failed while processing AI response, try again later..."


# TODO* GOOGLE SHEET API CONFIG
def setup_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Cek apakah ada environment variable untuk credentials
    google_creds_json = GOOGLE_CREDENTIALS

    if google_creds_json:
        # Gunakan credentials dari environment variable
        creds_dict = json.loads(google_creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # Fallback ke file credentials.json untuk development
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

    client = gspread.authorize(creds)
    return client

# TODO* SAVE TELEGRAM ID TO GOOGLE SHEET
def save_id_to_google_sheets(chat_id, username):
    
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

    # Menambahkan data ke baris berikutnya mulai dari baris kedua
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([chat_id, username, timestamp])
