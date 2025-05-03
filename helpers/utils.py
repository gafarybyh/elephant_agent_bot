from babel.numbers import format_currency

# TODO* SPLIT TEXT FOR TELEGRAM MESSAGES
def split_text(text, max_length=4096):
   
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

# TODO* FORMAT CURRENCY VALUE TO USD
def format_to_usd(value):
    return format_currency(value, 'USD', locale='en_US')