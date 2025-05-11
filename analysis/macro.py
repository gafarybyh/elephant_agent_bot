from helpers.api_helpers import fetch_financialjuice_feed, get_gemini_response_v2, fetch_calendar_economy
from datetime import datetime
import re
from config.app_config import logger

# TODO* CLASSIFY AND FORMAT NEWS
def classify_and_format_news(feed):

    us_keywords = [
    "fed", "fomc", "pce", "cpi", "ppi", "core inflation", "rate hike", "rate cut",
    "dot plot", "tightening", "easing", "nfp", "nonfarm", "jobless claims", "jolts",
    "payroll", "unemployment", "employment", "labor market", "treasury", "bond yields",
    "yields", "bonds", "dollar", "usd", "fiscal", "government shutdown", "budget deal",
    "retail sales", "consumer confidence", "ism", "pmi", "gdp", "gdi", "spending",
    "biden", "trump", "white house", "congress", "debt ceiling", "fiscal policy"
    ]

    china_keywords = [
    "china", "beijing", "xi jinping", "li qiang", "pboe", "pboc", "stimulus",
    "real estate", "property sector", "property crisis", "evergrande", "country garden",
    "local government debt", "shadow banking", "yuan", "soes", "manufacturing", "exports",
    "economic support", "infrastructure boost", "liquidity support"
    ]

    global_keywords = [
    "ecb", "europe", "eurozone", "boe", "boj", "boc", "rba", "rbnz",
    "germany", "france", "uk", "japan", "canada", "australia", "new zealand", "switzerland",
    "turkey", "singapore", "inflation", "disinflation", "deflation",
    "geopolitical", "ukraine", "russia", "iran", "israel", "middle east", "nato",
    "opec", "oil", "crude", "energy prices", "supply shock", "commodity", "brent", "conflict",
    "tensions", "ceasefire", "war", "missile", "gaza", "hezbollah", "houthis", "yemen",
    "eur", "gbp", "jpy", "cad", "aud", "nzd", "chf"
    ]

    us_locations = [
    "united states", "us", "america", "usa", "washington", "new york", "fed", "fomc", "yellen",
    "biden", "trump", "white house", "congress"
    ]
    china_locations = [
    "china", "beijing", "shanghai", "xi jinping", "pboe", "pboc", "chinese"
    ]
    global_locations = [
    "europe", "germany", "france", "uk", "england", "london",
    "japan", "tokyo", "canada", "ottawa", "australia", "sydney", "new zealand",
    "switzerland", "zurich", "turkey", "ankara", "singapore", "opec",
    "middle east", "iran", "israel", "russia", "ukraine", "saudi", "gaza", "hezbollah", "yemen", "swiss", "turkish"
    ]

    def build_pattern(keywords):
        return re.compile(r'\b(' + '|'.join(map(re.escape, keywords)) + r')\b', re.IGNORECASE)


    us_pattern = build_pattern(us_keywords)
    china_pattern = build_pattern(china_keywords)
    global_pattern = build_pattern(global_keywords)
    
    us_location_pattern = build_pattern(us_locations)
    china_location_pattern = build_pattern(china_locations)
    global_location_pattern = build_pattern(global_locations)

    us_news, china_news, global_news = [], [], []

    for item in feed.get('items', []):
        title = item.get('title', '').removeprefix('FinancialJuice: ').strip()
        published = item.get('pubDate', '')
        formatted_title = f"• {title} ({published})"
       
        is_us = us_pattern.search(title)
        is_china = china_pattern.search(title)
        is_global = global_pattern.search(title)

        if is_us and us_location_pattern.search(title):
            us_news.append(formatted_title)
        elif is_china and china_location_pattern.search(title):
            china_news.append(formatted_title)
        elif is_global and global_location_pattern.search(title):
            global_news.append(formatted_title)
        else:
            if us_location_pattern.search(title):
                us_news.append(formatted_title)
            elif china_location_pattern.search(title):
                china_news.append(formatted_title)
            elif global_location_pattern.search(title):
                global_news.append(formatted_title)
            else:
                global_news.append(formatted_title)

    return us_news, china_news, global_news


# TODO* GENERATE MACRO PROMPT
def generate_macro_prompt(us_news: list = None, china_news: list = None, global_news: list = None, calendar_news: list = None, user_question=None):
    """Generate a prompt for the Gemini model to analyze macro news."""
    # Join the news data with newlines outside the f-string to avoid backslash issues
    
    if user_question is None or user_question.strip() == "":
        user_question = "What is crypto sentiment of today's news?"
    
    us_news_text = "\n".join(us_news[:20]) if us_news else "• None"
    china_news_text = "\n".join(china_news[:20]) if china_news else "• None"
    global_news_text = "\n".join(global_news[:20]) if global_news else "• None"
    calendar_news_text = "\n".join(calendar_news[:20]) if calendar_news else "• None"
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""
You are a professional macroeconomic analyst specializing in cryptocurrency, high-risk assets and gold (safe haven asset). Generate a concise macro outlook for active traders based on the following headlines.

User Question: {user_question}
Current Time: {current_time}

US News:
{us_news_text}

China News:
{china_news_text}

Global News:
{global_news_text}

Economic Calendar (USD-focused):
{calendar_news_text}

Rules:
    - Prioritize categories: central bank policy (Fed, ECB, etc), inflation (CPI, PPI), labor market (NFP, unemployment), GDP, liquidity shifts, financial conditions, geopolitical tensions
    - Focus only on *latest, medium to high impact headlines especially US* relevant to risk-on/risk-off asset or user question asset context
    - Be concise, objective, and use Telegram format
    - Use simple, non-technical language that general audience can understand
    - Briefly explain financial terms when first mentioned (e.g., "CPI (Consumer Price Index, a measure of inflation)")
    - Translate market jargon into plain language (e.g., instead of "hawkish Fed stance" say "Fed's aggressive approach to fighting inflation")

Pre-check:
    - If the user's question is NOT about macro economic news or market sentiment, respond with: "Sorry, this command (/macro) is only for analyzing macroeconomic news and market sentiment. Please ask about economic news, market conditions, or investment outlook."
    - Always reply in the same language as the user's question (User Question: {user_question})

Respond using this format (max 15 lines):

    🌍 *[Macro Outlook title]*

    📉 *Market Sentiment:* [Simple explanation of what this means for investors, is market sentiment condition on risk-on or risk-off asset?]

    🔑 *Key Driver:*
    • 🇺🇸 *US:* [Most relevant US headline(s) in simple terms]
    • 🇨🇳 *China:* [Most relevant China headline(s) in simple terms]
    • 🌐 *Global:* [Most relevant global headline(s) in simple terms]
    • 📊 *Calendar:* [Important upcoming economic calendar events explained simply]

    💡 *What This Means:*
    [Simple explanation of how these events might affect crypto, gold, or investments]

    ⚖️ *What to Watch:*
    • *Positive Possibility:* [Potential good key drivers in simple terms and the most likely affected asset class]
    • *Risk to Consider:* [Potential bad key drivers in simple terms and the most likely affected asset class]

    🎯 *Suggestion:* [Simple asset allocation idea, e.g. "Lean defensive until CPI release", and brief reasoning why]

Respond only with the formatted analysis or the fallback message. No extra commentary.
"""

# ⚖️ What to Watch:
# • Positive Possibility: [Brief and clear explanation of a key positive macro driver and its potential effect. Include the most relevant asset class impacted.]
# • Risk to Consider: [Brief and clear explanation of a key downside risk and its potential effect. Include the most relevant asset class impacted.]

# TODO* FILTER CALENDAR ECONOMY DATA
def filtered_calendar_economy():
    calendar_data = fetch_calendar_economy()

    if calendar_data is None:
        return "Error: Failed to fetch calendar economy data, try again later..."

    # Filter: country = USD, impact = MEDIUM or HIGH
    filtered_data = [
        event for event in calendar_data
        if event.get('country') == 'USD' and event.get('impact') in ['Medium', 'High', 'All']
    ]

    # Sort berdasarkan 'date' (format: "2025-05-01 13:30:00")
    def safe_date_key(event):
        try:
            date_str = event.get('date')
            if date_str:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return datetime.min  # Default date for items without a date
        except (ValueError, TypeError):
            return datetime.min  # Default for invalid date formats

    sorted_data = sorted(filtered_data, key=safe_date_key)

    calendar_news = []

    for event in sorted_data:
        title = event.get('title', 'No Title')
        country = event.get('country', 'Unknown')
        date = event.get('date', 'No Date')
        impact = event.get('impact', 'Unknown')
        forecast = event.get('forecast', 'N/A')
        previous = event.get('previous', 'N/A')

        calendar_info = f"• {title} ({date}) | Country: {country}, Impact: {impact}, Forecast: {forecast}, Prev: {previous}"

        calendar_news.append(calendar_info)

    return calendar_news

# TODO* ANALYZE MACRO NEWS
def analyze_macro_news(user_query):
    try:
        raw_news = fetch_financialjuice_feed()

        if raw_news is None:
            return "Error: Failed to fetch news data, try again later..."

        # Check if raw_news is a dictionary and has the expected structure
        if not isinstance(raw_news, dict) or 'items' not in raw_news:
            return "Error: Unexpected format from news feed, try again later..."

        us_news, china_news, global_news = classify_and_format_news(raw_news)

        calendar_news = filtered_calendar_economy()

        # Check if calendar_news is an error message (string)
        if isinstance(calendar_news, str):
            # If it's an error message, we can still proceed with empty calendar data
            logger.warning(f"Calendar data error: {calendar_news}. Proceeding with empty calendar data.")
            calendar_news = []

        prompt = generate_macro_prompt(us_news, china_news, global_news, calendar_news, user_question=user_query)

        return get_gemini_response_v2(prompt)
    except Exception as e:
        logger.error(f"Error in analyze_macro_news: {e}")
        return f"Error analyzing macro news: {str(e)[:100]}... Please try again later."


# Keywords for filtering
# relevant_keywords = [
#     "fed", "fomc", "ecb", "boe", "boj", "interest rate", "rate hike", "rate cut", "tightening", "easing", "hawkish", "dovish", "pivot", "central bank", "cpi", "ppi", "gdp", "nfp", "unemployment", "payroll", "jobless claims", "pce", "core inflation", "retail sales", "consumer confidence", "housing starts", "ism", "pmi", "manufacturing", "liquidity", "risk", "risk-off", "risk-on", "recession", "credit", "default", "banking crisis", "china", "taiwan", "trump", "biden", "tariffs", "trade war", "regulation", "crypto regulation", "sec", "lawsuit", "bond yields", "dollar index", "usd", "vix", "volatility", "tech stocks", "equities", "bitcoin", "ethereum", "crypto", "cryptocurrency", "etf", "spot etf", "blackrock", "sec approval",  "coinbase", "binance"
#     ]

# MACRO_PROMPT_1 = """
#     You are a professional macroeconomic analyst specializing in cryptocurrency and high-risk assets. Create a concise macro analysis for traders.

#     News:
#     {all_macro_news}

#     User Question: {user_question}

#     Rules:
#     - Prioritize category: central bank policy (Fed, ECB, etc), inflation data (CPI, PPI), unemployment or job market reports (NFP), growth projections (GDP), financial conditions, liquidity shifts, and geopolitical tensions.
#     - Focus only on latest high-impact news
#     - Be direct and concise
#     - Output in telegram format
#     - Detect and reply in the same language as the user’s question

#     Format response as:
#     🌍 *Macro Outlook*

#     📊 Impact: [Bullish/Neutral/Bearish]

#     🔥 Key Drivers:
#     • [Category]: [Top most important headlines]

#     💡 Summary:
#     [3-5 lines max about market impact]

#     ⚖️ Risk Factors:
#     • Upside: [Key bullish catalyst]
#     • Downside: [Key bearish risk]

#     📉 *Dovish/Hawkish Scale:* [X/10] → [Short impact on crypto market] (Scale: 0 = Extremely Dovish, 10 = Extremely Hawkish)

#     ⚠️ Main Risk: [One key risk]

#     🎯 Action: [Risk On/Risk Off] [One clear trading suggestion]

#     Keep total response under 15 lines for readability.
#     """

# MACRO_PROMPT_2 = """
# You are a professional macroeconomic analyst with deep expertise in high-risk assets such as cryptocurrencies, tech stocks, and emerging markets. Your job is to analyze macroeconomic news headlines and provide a concise outlook for traders.

# News Headlines:
#     {all_macro_news}

# User Question (optional):
#     {user_question}

# Instructions:
#     - If no specific question is asked, assume the user wants a daily macro sentiment update for crypto positioning.
#     - Prioritize key macro themes: central bank policy (Fed, ECB, BOJ), inflation (CPI, PPI), jobs (NFP, unemployment), GDP, financial conditions (liquidity, credit), and geopolitical risks.
#     - First, classify each headline as Bullish / Bearish / Neutral.
#     - Group them by macro category (e.g., Inflation, Fed, Geopolitics).
#     - Count the sentiment distribution and use it to guide your final impact assessment.
#     - Ignore minor regional news unless it directly impacts global liquidity, central banks, or financial markets.
#     - Be concise and signal-driven — no fluff.
#     - Output in telegram format.
#     - Detect the language of the user question and reply in the same language.

# Output Format:

#     🌍 *Macro Outlook*

#     📊 *Impact:* [Bullish / Bearish / Neutral]

#     📶 *Confidence Level:* [High / Medium / Low] → Based on consistency and volume of impactful headlines

#     🔥 *Key Drivers:*
#     • [Category 1]: [Top headline + its impact]
#     • [Category 2]: [Top headline + its impact]
#     • ...

#     💡 *Summary:*
#     [2-4 line analysis of the overall macro picture and its implications for crypto or risk assets]

#     ⚖️ *Risk Balance:*
#     • *Upside Catalyst:* [One main bullish force]
#     • *Downside Risk:* [One main bearish threat]

#     🧭 *Dovish/Hawkish Scale:* [X/10] → [Short-term crypto bias] (Scale: 0 = Extremely Dovish, 10 = Extremely Hawkish)

#     🎯 *Positioning:* *[Risk-On / Risk-Off]* → [1 clear trading insight or asset allocation suggestion]

# """


# BACKUP MY PROMPT
# """
# You are a professional macroeconomic analyst specializing in cryptocurrency, gold, and high-risk assets. Generate a concise macro outlook for active traders based on the following headlines.

# User Question: {user_question}
# Current Time: {current_time}

# US News:
# {us_news_text}

# China News:
# {china_news_text}

# Global News:
# {global_news_text}

# Calendar Economy:
# {calendar_news_text}

# Rules:
#     - Prioritize categories: central bank policy (Fed, ECB, etc), inflation (CPI, PPI), labor market (NFP, unemployment), GDP, liquidity shifts, financial conditions, geopolitical tensions
#     - Focus only on *latest, medium to high impact headlines* relevant to crypto/gold/risk sentiment
#     - Be concise, objective, and use Telegram format
#     - Detect and reply in the same language as the user's question

# Respond using this format (max 15 lines):

#     🌍 *Macro Outlook*

#     📉 *Dovish/Hawkish Scale:* [X/10] → [Summary of short-term market bias on risk-on or risk-off assets] (0 = Extremely Dovish, 10 = Extremely Hawkish)

#     🔑 Key Drivers:
#     • 🇺🇸 US: [Most relevant US headline(s)]
#     • 🇨🇳 China: [Most relevant China headline(s)]
#     • 🌐 Global: [Most relevant global headline(s)]
#     • 📊 Calendar: [Analysis of upcoming economic events or past events]

#     💡 Summary:
#     [Short and direct summary of how these events affect crypto, gold, or general risk assets]

#     ⚖️ Risk Factors:
#     • Upside: [Possible bullish catalyst]
#     • Downside: [Most critical bearish risk]

#     🎯 Action: [Risk-On / Risk-Off] → [Tactical trading idea or asset allocation suggestion]
    
# Respond only with the formatted analysis or the fallback message. No extra commentary.
# """