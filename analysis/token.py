import requests
import math

def fetch_data():
    url = "https://raynor-api.gafarybyh.workers.dev/sheets/1PW67I8_1IFuvz5GBe-Gl8skCLzylRlOR8IWvv_mxCvI/Tokens"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def categorize_market_cap(market_cap):
    if market_cap > 10_000_000_000:
        return 'largeCap'
    elif market_cap > 1_000_000_000:
        return 'midCap'
    elif market_cap > 100_000_000:
        return 'smallCap'
    else:
        return 'microCap'

def calculate_iqr(data):
    sorted_data = sorted(data)
    n = len(sorted_data)
    def percentile(p):
        k = (n - 1) * p
        f = int(k)
        c = k - f
        if f + 1 < n:
            return sorted_data[f] + (sorted_data[f + 1] - sorted_data[f]) * c
        else:
            return sorted_data[f]
    q1 = percentile(0.25)
    q3 = percentile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return lower_bound, upper_bound

def detect_outliers():
    data = fetch_data()
    categories = {'largeCap': [], 'midCap': [], 'smallCap': [], 'microCap': []}
    tokens_by_category = {'largeCap': [], 'midCap': [], 'smallCap': [], 'microCap': []}

    for item in data:
        market_cap = item.get('market_cap')
        mcap_change = item.get('market_cap_change_percentage_24h')
        if market_cap is None or mcap_change is None:
            continue
        category = categorize_market_cap(market_cap)
        categories[category].append(mcap_change)
        tokens_by_category[category].append({
            'name': item.get('name'),
            'market_cap': market_cap,
            'market_cap_change_percentage_24h': mcap_change
        })

    outliers = []
    for category, changes in categories.items():
        if not changes:
            continue
        lower, upper = calculate_iqr(changes)
        for token in tokens_by_category[category]:
            change = token['market_cap_change_percentage_24h']
            if change < lower or change > upper:
                outliers.append({
                    'name': token['name'],
                    'category': category,
                    'market_cap': token['market_cap'],
                    'market_cap_change_percentage_24h': change
                })

    return outliers

if __name__ == "__main__":
    outlier_tokens = detect_outliers()
    for token in outlier_tokens:
        print(f"{token['name']} | Category: {token['category']} | Market Cap: {token['market_cap']} | Market Cap Change 24h: {token['market_cap_change_percentage_24h']}%")


def calculate_outlier(data):
    if not data:
        raise ValueError("Array data tidak boleh kosong.")

    # Salin dan urutkan data
    data = sorted(data)

    # Fungsi untuk menghitung kuartil
    def get_quartile(sorted_data, quartile):
        pos = (len(sorted_data) - 1) * quartile
        base = int(math.floor(pos))
        rest = pos - base
        next_val = sorted_data[base + 1] if base + 1 < len(sorted_data) else sorted_data[base]
        return sorted_data[base] + rest * (next_val - sorted_data[base])

    Q1 = get_quartile(data, 0.25)
    Q3 = get_quartile(data, 0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.2 * IQR
    upper_bound = Q3 + 1.2 * IQR

    # Hitung rata-rata
    mean = sum(data) / len(data)

    # Varians dan standar deviasi
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = math.sqrt(variance)

    # Z-score
    z_scores = [(x - mean) / std_dev for x in data]

    # Fungsi untuk menghitung persentil
    def get_percentile(sorted_data, percentile):
        index = math.ceil(percentile * len(sorted_data)) - 1
        return sorted_data[index]

    percentile_90 = get_percentile(data, 0.9)

    outliers = [x for x in data if x < lower_bound or x > upper_bound]
    tokens_above_p90 = [x for x in data if x > percentile_90]

    return {
        "Q1": Q1,
        "Q3": Q3,
        "IQR": IQR,
        "lowerBound": lower_bound,
        "upperBound": upper_bound,
        "zScores": z_scores,
        "percentile90": percentile_90,
        "tokensAbovePercentile90": tokens_above_p90,
        "outliers": outliers,
    }
