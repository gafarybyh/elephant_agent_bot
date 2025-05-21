from helpers.utils import format_currency
from analysis.cap_analysis import detect_early_momentum_v2
from datetime import datetime

def format_token_summary(token, index=None):
    """Format ringkasan token untuk pesan Telegram."""
    try:
        name = token.get("Tokens", "N/A")
        
        # Pastikan semua nilai numerik dikonversi dengan benar
        mcap = float(token.get("Market Cap", 0))
        mcap_change = float(token.get("Market Cap (Change 24h)", 0))
        price_change_24h = float(token.get("Price Changes 24h", 0))
        price_change_7d = float(token.get("Price Changes 7d", 0))
        total_volume = float(token.get("Total Volume", 0))
        turnover = float(token.get("Turnover Score", 0))
        
        # Pastikan VMR dikonversi dengan benar
        if "VMR" in token:
            vmr = float(token.get("VMR", 0)) * 100
        else:
            vmr = float(token.get("Hype Activity", 0))
            
        volatility = float(token.get("Volatility Score", 0))
        score = float(token.get("Early Momentum Score", 0))
        # strength = token.get("Momentum Strength", "Unknown")
        
        # Pastikan momentum_days adalah integer
        momentum_days = int(token.get("Momentum Duration", 1))
        momentum_type = str(token.get("Momentum Type", ""))
        
        # Pilih emoji berdasarkan tipe momentum
        if "New Strong" in momentum_type:
            momentum_emoji = "🚀"  # Momentum baru dan kuat
        elif "Established Strong" in momentum_type:
            momentum_emoji = "⭐"  # Momentum kuat berkelanjutan
        elif "New" in momentum_type:
            momentum_emoji = "🆕"  # Momentum baru
        elif "Emerging" in momentum_type:
            momentum_emoji = "🌱"  # Momentum yang baru muncul
        elif "Fading" in momentum_type:
            momentum_emoji = "📉"  # Momentum yang melemah
        else:
            momentum_emoji = "⏱️"  # Default
        
        # Determine signal strength
        if score >= 0.8:
            signal = "Strong 🔥🔥"
        elif score >= 0.7:
            signal = "Strong 🔥"
        elif score >= 0.5:
            signal = "Medium 📈"
        elif score >= 0.3:
            signal = "Weak ⚠️"
        else:
            signal = "Watch 👀"

        # Add outlier indicator - pastikan is_outlier adalah boolean
        is_outlier = bool(token.get("Is Outlier", False))
        if is_outlier:
            signal += "⭐"
 
        # Add rank indicator for top 3
        # Pastikan index adalah integer sebelum membandingkan
        if index is not None:
            index = int(index)
            rank_indicator = f"#{index+1} " if index < 3 else ""
        else:
            rank_indicator = ""
        
        # Format price changes with trend indicators
        price_24h_trend = "🟢" if price_change_24h > 0 else "🔴"
        price_7d_trend = "🟢" if price_change_7d > 0 else "🔴"
        
        if vmr > 50:
            hype_icon = "🔥"
        elif vmr > 30:
            hype_icon = "📈"
        elif vmr > 15:
            hype_icon = "👀"
        else:
            hype_icon = ""
        
        # Format for Telegram (using emoji and clear formatting)
        return (
            "```\n"
            f"{rank_indicator}*{name.upper()}*\n"
            f"💰 MCAP: {format_currency(mcap)} (*{mcap_change:.2f}%*)\n"
            f"💲 Price 24h: *{price_change_24h:.2f}%* {price_24h_trend}\n"
            f"💲 Price 7d: *{price_change_7d:.2f}%* {price_7d_trend}\n"
            f"📊 Vol: {format_currency(total_volume)} ({vmr:.2f}% Hype) {hype_icon}\n"
            f"🔄 Turnover: *{turnover:.2f}*\n"
            f"📈 Volatility: *{volatility:.2f}*\n"
            f"{momentum_emoji} Momentum: *{momentum_days}d* ({momentum_type})\n"
            f"🏆 Score: *{score:.2f}*\n"
            f"📝 Strength: {signal}\n"
            "```"
        )
    except Exception as e:
        # Tambahkan debugging untuk melihat token yang menyebabkan error
        error_msg = f"Error formatting token: {e}\n"
        try:
            # Coba print beberapa informasi kunci untuk debugging
            error_msg += f"Token name: {token.get('Tokens', 'N/A')}\n"
            error_msg += f"Index: {index}, Type: {type(index)}\n"
            
            # Cek tipe data dari beberapa field kunci
            for key in ["Market Cap", "Price Changes 24h", "Price Changes 7d", "Momentum Duration"]:
                value = token.get(key, "N/A")
                error_msg += f"{key}: {value}, Type: {type(value)}\n"
        except:
            pass
        
        return error_msg 

def format_category_tokens(category_name, limit=15):
    """Format token dengan early momentum untuk kategori tertentu."""
    tokens = detect_early_momentum_v2(category_name)
    
    if not tokens:
        return f"No tokens with early momentum detected in {category_name} category.\n"

    result = f"*TOP {category_name.upper()} TOKENS WITH MOMENTUM*\n\n"
    
    for i, token in enumerate(tokens[:limit]):
        result += format_token_summary(token, i) + "\n"

    return result

def format_detailed_analysis(token, index):
    """Format analisis detail token untuk Telegram."""
    try:
        name = token.get("Tokens", "N/A")
        mcap = token.get("Market Cap", 0)
        category = token.get("Market Cap Category", "Unknown")
        score = token.get("Early Momentum Score", 0)
        
        return (
            f"*{index+1}. {name}* ({format_currency(mcap)}, {category})\n"
            f"*Overall Momentum Score:* {score:.2f} ({token.get('Momentum Strength', 'Unknown')})\n\n"
            f"*Component Scores:*\n"
            f"- MCAP Change: {token.get('MCAP Score', 0):.2f}\n"
            f"- Turnover: {token.get('Turnover Score', 0):.2f}\n"
            f"- Hype Activity: {token.get('Hype Score', 0):.2f}\n"
            f"- Price Action: {token.get('Price Score', 0):.2f}\n"
            f"- Volume Change: {token.get('Volume Score', 0):.2f}\n\n"
            f"*Raw Metrics:*\n"
            f"- Market Cap: {format_currency(mcap)}\n"
            f"- Market Cap Change 24h: {token.get('Market Cap (Change 24h)', 0):.2f}%\n"
            f"- Volume/MCAP Ratio: {token.get('VMR', 0) * 100:.2f}%\n"
            f"- Volatility: {token.get('Volatility', 0):.2f}%\n\n"
        )
    except Exception as e:
        return f"Error displaying detailed analysis for token {index+1}: {e}\n"

def generate_momentum_report():
    """Generate a comprehensive momentum report for all market cap categories in Telegram format."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"*EARLY MOMENTUM TOKEN REPORT - {timestamp}*\n"
    report += "Tokens showing early signs of momentum across market cap categories\n\n"

    # Store all tokens for later analysis
    all_category_tokens = {}

    # Get tokens for each category
    all_category_tokens["largeCap"] = detect_early_momentum_v2("largeCap")
    all_category_tokens["midCap"] = detect_early_momentum_v2("midCap")
    all_category_tokens["smallCap"] = detect_early_momentum_v2("smallCap")
    all_category_tokens["microCap"] = detect_early_momentum_v2("microCap")
    
    # Add category summaries to report
    for category in ["largeCap", "midCap", "smallCap", "microCap"]:
        report += format_category_tokens(category) + "\n"

    # Add detailed analysis section
    report += "*DETAILED ANALYSIS OF TOP MOMENTUM TOKENS*\n\n"
    
    # Combine all categories and deduplicate tokens
    all_tokens = []
    seen_tokens = set()

    for category, tokens in all_category_tokens.items():
        if not tokens:
            continue
        for token in tokens:
            token_name = token.get("Tokens", "")
            if token_name and token_name not in seen_tokens:
                seen_tokens.add(token_name)
                all_tokens.append(token)

    # Sort by momentum score and get top 5
    top_tokens = sorted(all_tokens, key=lambda x: x.get("Early Momentum Score", 0), reverse=True)[:5]

    if not top_tokens:
        report += "No tokens with significant momentum detected for detailed analysis.\n"
        return report, all_category_tokens

    for i, token in enumerate(top_tokens):
        report += format_detailed_analysis(token, i)

    return report, all_category_tokens







