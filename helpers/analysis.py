from babel.numbers import format_currency
from .api_helpers import fetch_data_sector, get_gemini_response, fetch_financialjuice_feed
from config.prompt import (MACRO_PROMPT_1, SECTOR_PROMPT)
from config.app_config import logger


# TODO* SPLIT TEXT FOR TELEGRAM MESSAGES
def split_text(text, max_length=4096):
   
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

# TODO* FORMAT CURRENCY VALUE TO USD
def format_to_usd(value):
    return format_currency(value, 'USD', locale='en_US')

# TODO* ANALYZE SECTOR
def analyze_data_sector(user_query):

    try:
        data = fetch_data_sector()

        if data is None:
            return "Error: Failed to fetch sector data."
        
        # Validate data structure
        if 'values' not in data or len(data['values']) < 2:
            return "Sector data ERROR or data is not in the expected format ."

        sector_data = data['values'][1:]  # Ignore header

        # Format data untuk analisis - dikelompokkan berdasarkan sektor
        sectors_formatted = []
        for row in sector_data:
            # Validasi struktur row
            if len(row) < 5:
                continue  # Skip row yang tidak lengkap

            try:
                sector_name = row[0]
                volume = format_to_usd(float(row[1]))
                market_cap = format_to_usd(float(row[2]))
                market_cap_change = f"{float(row[3]):.2f}%"
                activity = f"{float(row[4]):.2f}%"

                sector_info = f"- {sector_name}, Volume: {volume}, Market Cap: {market_cap}, MCap Change: {market_cap_change}, Activity {activity}"
                
                sectors_formatted.append(sector_info)
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Skipping row due to formatting error: {e}")
                continue

        if not sectors_formatted:
            return "No sector data to analyze."

        # Gabungkan semua data sektor
        all_sectors_data = "\n".join(sectors_formatted)

        # Prompt yang meminta AI untuk mendeteksi dan menyesuaikan bahasa
        prompt = SECTOR_PROMPT

        # Format data untuk analisis
        formatted_text = prompt.format(
            all_sectors_data=all_sectors_data,
            user_question=user_query
        )

        # Kirim prompt ke Gemini
        return get_gemini_response(formatted_text)
    except KeyError as e:
        logger.error(f"Error: Missing expected key in SECTOR DATA: {e}")
        return f"Error: Missing expected key in SECTOR DATA: ({e})"
    except ValueError as e:
        logger.error(f"Error: While processing data type value in SECTOR DATA:  {e}")
        return f"Error: While processing data type value in SECTOR DATA: ({e})"
    except Exception as e:
        logger.error(f"Error: occurred while processing SECTOR DATA: {e}")
        return f"Error: occurred while processing SECTOR DATA: {e}"
    
# TODO* ANALYZE MACRO
def analyze_data_macro(user_query):
    try:
        financialjuice = fetch_financialjuice_feed()
        
        if financialjuice is None:
            return "Error: Failed to fetch Financial Juice feed."
        
        macro_formatted = []
        
        for news in financialjuice:
            if 'published' not in news or 'title' not in news:
                logger.warning("Skipping news item (missing title or published date)")
                continue
            news_data = f"- [{news['published']}] {news['title']}"
            macro_formatted.append(news_data)
        
        if not macro_formatted:
            logger.warning("No valid macroeconomic news found to analyze.")
            return "There is no macro data to analyze."

        all_macro = "\n".join(macro_formatted)
        
        prompt = MACRO_PROMPT_1
        
        # Format prompt
        # Placeholder {all_macro_news} & {user_question} inside prompt
        formatted_prompt = prompt.format(
            all_macro_news=all_macro,
            user_question=user_query
        )
        
        return get_gemini_response(formatted_prompt)
        
    except Exception as e:
        logger.error(f"Error: Unexpected error while analyzing MACRO: {e}")
        return f"Error occurred while analyzing MACRO: {e}"