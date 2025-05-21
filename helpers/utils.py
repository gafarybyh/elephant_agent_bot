from babel.numbers import format_currency

# TODO* SPLIT TEXT FOR TELEGRAM MESSAGES
def split_text(text, max_length=4096):
   
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

# TODO* FORMAT CURRENCY VALUE TO USD
def format_to_usd(value):
    return format_currency(value, 'USD', locale='en_US')

"""
Module untuk fungsi-fungsi utilitas yang digunakan dalam analisis token.
"""
def parse_float(s):
    """Fungsi parsing yang lebih robust untuk mengkonversi string ke float.
    
    Handles various formats found in the JSON data:
    - Numbers with commas (e.g., "1,234.56")
    - Percentages (e.g., "12.34%")
    - Currency symbols (e.g., "$123.45")
    - Empty strings or None values
    - Already parsed numbers (int/float)
    
    Args:
        s: Nilai yang akan dikonversi ke float
        
    Returns:
        float: Nilai yang sudah dikonversi
    """
    try:
        # Handle None or empty values
        if s is None or (isinstance(s, str) and not s.strip()):
            return 0.0

        # If already a number, just convert to float
        if isinstance(s, (int, float)):
            return float(s)

        # Handle string representations
        if isinstance(s, str):
            # Remove currency symbols, commas, and percentage signs
            cleaned = s.replace('$', '').replace(',', '').replace('%', '')
            # Handle negative values with parentheses e.g. "(123.45)"
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            # Convert to float if not empty
            if cleaned.strip():
                return float(cleaned)

        # Default for any other case
        return 0.0
    except Exception as e:
        print(f"Error parsing value '{s}': {e}")
        return 0.0

def categorize_market_cap(market_cap):
    """Mengkategorikan token berdasarkan market cap.
    
    Args:
        market_cap (float): Nilai market cap token
        
    Returns:
        str: Kategori market cap (largeCap, midCap, smallCap, microCap)
    """
    if market_cap > 10_000_000_000:
        return 'largeCap'
    elif market_cap > 1_000_000_000:
        return 'midCap'
    elif market_cap > 100_000_000:
        return 'smallCap'
    else:
        return 'microCap'

def format_currency(value):
    """Memformat nilai market cap menjadi string yang mudah dibaca.
    
    Args:
        value (float): Nilai market cap
        
    Returns:
        str: String yang diformat (contoh: $1.23B, $45.67M)
    """
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    else:
        return f"${value:.2f}"
