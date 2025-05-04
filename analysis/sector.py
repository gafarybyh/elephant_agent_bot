from config.app_config import logger
from helpers.api_helpers import fetch_data_sector, get_gemini_response
from helpers.utils import format_to_usd

def generate_sector_prompt(all_sectors_data: list = None, user_question=None):
    """Generate a prompt for the Gemini model to analyze crypto sector performance."""
    
    # Default user question if not provided
    if user_question is None or user_question.strip() == "":
        user_question = "How does this crypto sector performing today?"

    # Join the sectors data with newlines outside the f-string to avoid backslash issues
    sectors_data_text = "\n".join(all_sectors_data) if all_sectors_data else "• None"

    return f"""
You are a professional crypto market analyst for a Telegram bot. Your task is to assess crypto sector performance based on the user's query and deliver concise, data-driven insights.

User Question: {user_question}

Sector Data:
{sectors_data_text}

Pre‐check:
    - If the user's question is NOT about crypto sector performance, respond with: "Sorry, this command (/sector) only for analyze crypto sector performance. Please ask about crypto sectors."

Instructions:
    - Answer in the same language as the user's question.
    - Start with a *bold* title and a one-sentence answer based on user's query context.
    - If the query names a specific sector, analyze only that sector.
    Otherwise, for all sectors:
        • Rank by Market Cap Change, Activity Growth, and Volume Spike.
    - For each sector:
        • Format **bold** sector names and metrics values.
        • Format currency values with "M" or "B" (million/billion).
        • Format percentage values with two decimal places.
        • Output in Telegram format:

        🚀 *[Sector Name]*
        📊 Volume: $[Volume]
        💰 Market Cap: $[Market Cap]
        📈 Mcap Change: [Market Cap Change]%
        🔥 Activity: [Activity]%
        🔍 *Insight*: [2 lines—
            • Line 1: precise momentum + relative context (vs mean/median or rank)
            • Line 2: brief reason + actionable suggestion
    - If no sector meets criteria, offer a brief suggestion (e.g., "No standout sectors—monitor top performers and market trends.").
    - Limit output to 10–12 lines for mobile readability.

Respond only with the formatted analysis or the fallback message. No extra commentary.
"""

# TODO* ANALYZE SECTOR
def analyze_sector(user_query):
    try:
        raw_sectors = fetch_data_sector()

        if raw_sectors is None or 'values' not in raw_sectors:
            return "Error: Failed to fetch sector data, or No 'values' field in sector data, try again later..."

        sector_data = raw_sectors['values'][1:]  # Ignore header at first index

        # Formatted Sectors
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

                sector_info = f"• {sector_name}, Volume: {volume}, Market Cap: {market_cap}, MCap Change: {market_cap_change}, Activity {activity}"

                sectors_formatted.append(sector_info)

            except (ValueError, IndexError) as e:
                logger.warning(f"Skipping row due to SECTOR formatting error: {e}")
                continue

        if not sectors_formatted:
            return "No sector data to analyze."


        prompt = generate_sector_prompt(all_sectors_data=sectors_formatted, user_question=user_query)

        return get_gemini_response(prompt)

    except KeyError as e:
        logger.error(f"Error: Missing expected key in SECTOR DATA: {e}")
        return f"Error: Missing expected key in SECTOR DATA: ({e})"
    except ValueError as e:
        logger.error(f"Error: While processing data type value in SECTOR DATA:  {e}")
        return f"Error: While processing data type value in SECTOR DATA: ({e})"
    except Exception as e:
        logger.error(f"Error: occurred while processing SECTOR DATA: {e}")
        return f"Error: occurred while processing SECTOR DATA: {e}"
