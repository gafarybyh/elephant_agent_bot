from helpers.api_helpers import fetch_financialjuice_feed, get_gemini_response, fetch_calendar_economy
from datetime import datetime
import re

# TODO* CLASSIFY AND FORMAT NEWS
def classify_and_format_news(feed):
    us_keywords = [
        "fed", "fomc", "pce", "cpi", "ppi", "core inflation", "rate hike", "rate cut", 
        "dot plot", "tightening", "easing", "nfp", "nonfarm", "jobless claims", 
        "payroll", "unemployment", "treasury", "bond yields", "dollar", "usd", 
        "retail sales", "consumer confidence", "ism", "pmi", "gdp", "financial conditions"
    ]

    china_keywords = [
        "china", "pboe", "pboc", "xi jinping", "stimulus", "property crisis", 
        "real estate", "liquidity", "yuan", "shadow banking", "evergrande"
    ]

    global_keywords = [
        "ecb", "europe", "eurozone", "germany", "france", "inflation", 
        "rate hike", "rate cut", "ukraine", "russia", "geopolitical", 
        "oil", "saudi", "middle east", "israel", "iran", "boj", "japan", "boe", "uk"
    ]
    
     # Compile regex patterns for each category
    def build_pattern(keywords):
        return re.compile(r'\b(' + '|'.join(map(re.escape, keywords)) + r')\b', re.IGNORECASE)

    us_pattern = build_pattern(us_keywords)
    china_pattern = build_pattern(china_keywords)
    global_pattern = build_pattern(global_keywords)

    us_news, china_news, global_news = [], [], []

    for item in feed:
        title = item.get('title', '')
        published = item.get('published', '')
        formatted_title = f"• {title} ({published})"

        if us_pattern.search(title):
            us_news.append(formatted_title)
        elif china_pattern.search(title):
            china_news.append(formatted_title)
        elif global_pattern.search(title):
            global_news.append(formatted_title)

    return us_news, china_news, global_news


# TODO* GENERATE MACRO PROMPT
def generate_macro_prompt(us_news: list = None, china_news: list = None, global_news: list = None, calendar_news: list = None, user_question="How does this impact crypto today?"):
    return f"""
You are a professional macroeconomic analyst specializing in cryptocurrency, gold, and high-risk assets. Generate a concise macro outlook for active traders based on the following headlines.

US News:
{"\n".join(us_news[:5]) or "• None"}

China News:
{"\n".join(china_news[:3]) or "• None"}

Global News:
{"\n".join(global_news[:3]) or "• None"}

Calendar Economy:
{"\n".join(calendar_news[:10]) or "• None"}

User Question: {user_question}

Rules:
    - Prioritize categories: central bank policy (Fed, ECB, etc), inflation (CPI, PPI), labor market (NFP, unemployment), GDP, liquidity shifts, financial conditions, geopolitical tensions
    - Focus only on *latest, high-impact headlines* relevant to crypto/gold/risk sentiment
    - Be concise, objective, and use Telegram format
    - Detect and reply in the same language as the user's question

Respond using this format (max 15 lines):

    🌍 *Macro Outlook*

    📊 Impact: [Bullish / Neutral / Bearish]

    🔑 Key Drivers:
    • 🇺🇸 US: [Most relevant US headline(s)]
    • 🇨🇳 China: [Most relevant China headline(s)]
    • 🌐 Global: [Most relevant global headline(s)]

    💡 Summary:
    [Short and direct summary of how these events affect crypto, gold, or general risk assets]

    ⚖️ Risk Factors:
    • Upside: [Possible bullish catalyst]
    • Downside: [Most critical bearish risk]

    📉 *Dovish/Hawkish Scale:* [X/10] → [Impact on crypto] (0 = Extremely Dovish, 10 = Extremely Hawkish)

    🎯 Action: [Risk On / Risk Off] → [Tactical trading idea]
"""

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
    sorted_data = sorted(
        filtered_data,
        key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S")
    )
    
    calendar_news = []
    
    for event in sorted_data:
        title = event.get('title')
        country = event.get('country')
        date = event.get('date')
        impact = event.get('impact')
        forecast = event.get('forecast')
        previous = event.get('previous')
        
        calendar_info = f"• {title} ({date}) | Country: {country}, Impact: {impact}, Forecast: {forecast}, Prev: {previous}"
        
        calendar_news.append(calendar_info)
        
    return calendar_news
    
# TODO* ANALYZE MACRO NEWS
def analyze_macro_news(user_query):
    raw_news = fetch_financialjuice_feed()
    
    if raw_news is None:
        return "Error: Failed to fetch news data, try again later..."

    us_news, china_news, global_news = classify_and_format_news(raw_news)
    
    calendar_news = filtered_calendar_economy()
    
    if not isinstance(calendar_news, list):
        return []

    prompt = generate_macro_prompt(us_news, china_news, global_news, calendar_news, user_question=user_query)
    
    return get_gemini_response(prompt)


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