import numpy as np
from helpers.utils import parse_float, categorize_market_cap
from helpers.api_helpers import fetch_data_token

def winsorize(values, limits=(0.05, 0.05)):
    """Membatasi nilai ekstrem pada persentil tertentu."""
    if not values or len(values) < 4:
        return values
    values_array = np.array(values)
    lower = np.percentile(values_array, limits[0] * 100)
    upper = np.percentile(values_array, (1 - limits[1]) * 100)
    return [min(max(x, lower), upper) for x in values]

# *DETECT OUTLIERS
def detect_outliers(values, method="iqr", threshold=1.5, sensitivity=1.0):
    """Deteksi outlier dengan metode statistik yang lebih robust dan sensitif.

    Args:
        values (list): List nilai yang akan dianalisis
        method (str): "iqr" (Inter-Quartile Range), "zscore", atau "hybrid"
        threshold (float): Batas untuk menentukan outlier (default 1.5 untuk IQR, 2.0 untuk z-score)
        sensitivity (float): Faktor pengali untuk meningkatkan sensitivitas deteksi (default 1.0)

    Returns:
        dict: Dictionary berisi informasi outlier dan nilai-nilai yang dinormalisasi
    """
    if not values or len(values) < 4:  # Minimal data untuk analisis statistik
        return {"outliers": [], "normalized": [0] * len(values), "ranks": [0] * len(values)}

    values_array = np.array(values)
    outliers = []
    normalized = []

    # Tambahkan ranking untuk mendeteksi token yang relatif lebih tinggi
    ranks = np.zeros(len(values))
    if len(values) > 1:  # Pastikan ada cukup data untuk ranking
        # Buat ranking berdasarkan nilai (1 = tertinggi)
        temp_ranks = (-values_array).argsort().argsort() + 1
        # Normalisasi ranking ke 0-1
        ranks = 1 - (temp_ranks - 1) / (len(values) - 1) if len(values) > 1 else np.ones(len(values))

    if method == "iqr" or method == "hybrid":
        # Metode IQR (Inter-Quartile Range) dengan sensitivitas yang ditingkatkan
        q1 = np.percentile(values_array, 25)
        q3 = np.percentile(values_array, 75)
        iqr = q3 - q1

        # Gunakan sensitivitas untuk menyesuaikan batas
        adjusted_threshold = threshold / sensitivity
        lower_bound = q1 - adjusted_threshold * iqr
        upper_bound = q3 + adjusted_threshold * iqr

        # Identifikasi outlier dengan sensitivitas yang ditingkatkan
        outliers = [x for x in values if x > upper_bound]

        # Normalisasi berdasarkan posisi dalam range dengan kurva eksponensial
        for val in values:
            if val <= lower_bound:
                normalized.append(0.0)
            elif val >= upper_bound:
                normalized.append(1.0)
            else:
                # Normalisasi non-linear untuk meningkatkan sensitivitas
                base_norm = (val - lower_bound) / (upper_bound - lower_bound)
                # Gunakan fungsi eksponensial untuk meningkatkan sensitivitas
                norm_val = np.power(base_norm, 1/sensitivity)
                normalized.append(min(1.0, max(0.0, norm_val)))

    elif method == "zscore":
        # Metode Z-Score dengan sensitivitas yang ditingkatkan
        mean = np.mean(values_array)
        std = np.std(values_array)

        # if std == 0:  # Hindari pembagian dengan nol
        if std <= np.finfo(float).eps:
            return {"outliers": [], "normalized": [0] * len(values), "ranks": ranks}

        zscores = [(x - mean) / std for x in values]

        # Identifikasi outlier dengan threshold yang disesuaikan
        adjusted_threshold = threshold / sensitivity
        outliers = [values[i] for i, z in enumerate(zscores) if z > adjusted_threshold]

        # Normalisasi berdasarkan z-score dengan sensitivitas yang ditingkatkan
        for z in zscores:
            if z <= 0:
                # Nilai di bawah rata-rata mendapat skor rendah
                norm_val = 0.5 * np.exp(sensitivity * z)
            else:
                # Nilai di atas rata-rata mendapat skor tinggi dengan kurva eksponensial
                norm_val = 0.5 + 0.5 * (1 - np.exp(-sensitivity * z))
            normalized.append(min(1.0, max(0.0, norm_val)))

    # Jika metode hybrid, gabungkan hasil IQR dan ranking
    if method == "hybrid":
        # Gabungkan normalized dengan ranks untuk hasil akhir
        # normalized = [0.7 * n + 0.3 * r for n, r in zip(normalized, ranks)]
        normalized = 0.7 * np.array(normalized) + 0.3 * ranks

    return {
        "outliers": outliers,
        "normalized": normalized,
        "ranks": list(ranks)
    }

# *DETECT EARLY MOMENTUM
def detect_early_momentum_v2(category_name):
    """Deteksi token dengan early momentum menggunakan analisis outlier yang ditingkatkan.
    
    Args:
        category_name (str): Kategori market cap yang akan dianalisis ("largeCap", "midCap", "smallCap", "microCap")
        
    Returns:
        list: Token dengan early momentum yang sudah diurutkan berdasarkan skor
    """
    # TODO===== TAHAP 1: PERSIAPAN DATA =====
    data = fetch_data_token()
    if not data or 'values' not in data:
        print("No valid data available for analysis")
        return []

    headers = data["values"][0]
    rows = data["values"][1:]
    tokens = []

    # Map column names to indices for faster access
    column_indices = {header: idx for idx, header in enumerate(headers)}

    # Check for required columns
    required_columns = ["Tokens", "Market Cap", "Total Volume", "Circulating Supply", "Market Cap (Change 24h)"]
    missing_columns = [col for col in required_columns if col not in column_indices]

    if missing_columns:
        print(f"Warning: Missing required columns for momentum analysis: {', '.join(missing_columns)}")
        print("Using available columns and estimating missing values.")

    # TODO===== TAHAP 2: EKSTRAKSI DAN KALKULASI METRIK TOKEN =====
    for row_idx, row in enumerate(rows):
        try:
            # Skip rows that are too short
            if len(row) < min(3, len(headers)):
                continue

            # Extend row if needed to match headers length
            if len(row) < len(headers):
                row = row + [""] * (len(headers) - len(row))

            # Create token data dictionary
            token_data = dict(zip(headers, row))
            token_name = token_data.get("Tokens", f"Unknown-{row_idx}")

            # Extract and parse market cap
            try:
                market_cap = parse_float(token_data.get("Market Cap", 0))
                if market_cap <= 0:
                    # Try to calculate from price and supply if available
                    price = parse_float(token_data.get("Price", 0))
                    circ_supply = parse_float(token_data.get("Circulating Supply", 0))
                    if price > 0 and circ_supply > 0:
                        market_cap = price * circ_supply
                        print(f"Calculated market cap for {token_name}: {market_cap}")
            except Exception as e:
                print(f"Error processing market cap for {token_name}: {e}")
                market_cap = 0

            # Determine category
            category = categorize_market_cap(market_cap)

            # Skip if not in requested category
            if category != category_name:
                continue

            # Extract and calculate metrics with robust error handling
            try:
                # *TOKEN METRICS
                volume = parse_float(token_data.get("Total Volume", 0))
                circ_supply = parse_float(token_data.get("Circulating Supply", 0))
                mcap_change = parse_float(token_data.get("Market Cap (Change 24h)", 0))
                price_change = parse_float(token_data.get("Price Changes 24h", 0))
                
                # Estimate volume change if not available
                volume_change = 0
                if "Total Volume" in token_data and "Market Cap" in token_data:
                    volume = parse_float(token_data.get("Total Volume", 0))
                    mcap = parse_float(token_data.get("Market Cap", 0))
                    if mcap > 0:
                        # Estimate volume change based on volume/mcap ratio
                        vmr = volume / mcap * 100
                        if vmr > 10:
                            volume_change = 30  # High change
                        elif vmr > 5:
                            volume_change = 15  # Medium change
                        elif vmr > 2:
                            volume_change = 5   # Low change

                        # If price is up and volume is high, volume likely increased
                        if price_change > 0 and vmr > 1:
                            volume_change = max(volume_change, price_change)

                # Calculate turnover (Volume/Circulating Supply)
                turnover = 0
                if "Turnover (% Cirulating Supply Traded)" in token_data and token_data["Turnover (% Cirulating Supply Traded)"]:
                    turnover = parse_float(token_data.get("Turnover (% Cirulating Supply Traded)", 0))
                elif circ_supply > 0:
                    turnover = (volume / circ_supply) * 100

                # Log-normalisasi untuk mengatasi perbedaan skala ekstrem
                if turnover > 0:
                    turnover = np.log1p(turnover)  # log(1+x) untuk menghindari log(0)

                # Calculate hype activity (Volume/Market Cap)
                hype_activity = 0
                if "Hype Activity" in token_data and token_data["Hype Activity"]:
                    hype_activity = parse_float(token_data.get("Hype Activity", 0))
                elif market_cap > 0:
                    hype_activity = (volume / market_cap) * 100

                # VMR is the same as Hype Activity / 100
                vmr = hype_activity / 100

                # Calculate price-volume correlation
                price_volume_correlation = 0.5  # Neutral default
                if price_change > 0 and volume_change > 0:
                    price_volume_correlation = 1.0  # Positive correlation
                elif price_change < 0 and volume_change < 0:
                    price_volume_correlation = 0.3  # Negative correlation

                # Get or estimate volatility
                volatility = parse_float(token_data.get("Volatility 24h", 0))
                if volatility == 0:
                    volatility = parse_float(token_data.get("Volatility", 0))
                    if volatility == 0 and price_change != 0:
                        volatility = abs(price_change)
                    else:
                        volatility = 1.0

                # Store all metrics in token data
                token_data["Market Cap"] = market_cap
                token_data["Market Cap Category"] = category
                token_data["Turnover"] = turnover
                token_data["Hype Activity"] = hype_activity
                token_data["Market Cap (Change 24h)"] = mcap_change
                token_data["Price Change 24h"] = price_change
                token_data["Volume Change 24h"] = volume_change
                token_data["Volatility"] = volatility
                token_data["VMR"] = vmr
                token_data["Price-Volume Correlation"] = price_volume_correlation

                tokens.append(token_data)

            except Exception as e:
                print(f"Error processing metrics for {token_name}: {e}")
                continue

        except Exception as e:
            print(f"Error processing row {row_idx}: {e}")
            continue

    if not tokens:
        return []

    # TODO===== TAHAP 3: ANALISIS OUTLIER DAN NORMALISASI =====
    # * Set sensitivity based on market cap category
    sensitivity_map = {
        "largeCap": 1.0,    # Large caps need less sensitivity adjustment
        "midCap": 1.2,      # Mid caps need moderate sensitivity
        "smallCap": 1.5,    # Small caps need higher sensitivity
        "microCap": 2.0     # Micro caps need highest sensitivity
    }
    sensitivity = sensitivity_map.get(category_name, 1.0)

    # Extract metrics for analysis
    # Use Max to avoid calculate negative values
    mcap_changes = [max(0, t["Market Cap (Change 24h)"]) for t in tokens]
    turnovers = winsorize([t["Turnover"] for t in tokens])
    hypes = [t["Hype Activity"] for t in tokens]
    price_changes = [max(0, t.get("Price Change 24h", 0)) for t in tokens]
    volume_changes = [max(0, t.get("Volume Change 24h", 0)) for t in tokens]
    volatilities = [t["Volatility"] for t in tokens]

    # Detect outliers and normalize with hybrid method and adjusted sensitivity
    mcap_analysis = detect_outliers(mcap_changes, method="hybrid", threshold=1.5, sensitivity=sensitivity)
    turnover_analysis = detect_outliers(turnovers, method="hybrid", threshold=1.5, sensitivity=sensitivity)
    hype_analysis = detect_outliers(hypes, method="hybrid", threshold=1.5, sensitivity=sensitivity)
    price_analysis = detect_outliers(price_changes, method="hybrid", threshold=1.5, sensitivity=sensitivity)
    volume_analysis = detect_outliers(volume_changes, method="hybrid", threshold=1.5, sensitivity=sensitivity)
    volatility_analysis = detect_outliers(volatilities, method="hybrid", threshold=1.5, sensitivity=sensitivity)

    # TODO===== TAHAP 4: KALKULASI SKOR MOMENTUM =====
    # Category-specific weights for different metrics
    # Use weights because every Market cap category has different characteristics, e.g.:
    # - Large caps are more stable, so we should give less weight to price and volume changes
    # - Small caps are more volatile, so we should give more weight to price and hype
    weights = {
        "largeCap": {
            "mcap_chg": 0.25, "turnover": 0.20, "hype": 0.25,
            "price": 0.10, "volume": 0.10, "volatility": 0.10
        },
        "midCap": {
            "mcap_chg": 0.20, "turnover": 0.20, "hype": 0.30,
            "price": 0.10, "volume": 0.10, "volatility": 0.10
        },
        "smallCap": {
            "mcap_chg": 0.15, "turnover": 0.20, "hype": 0.30,
            "price": 0.15, "volume": 0.10, "volatility": 0.10
        },
        "microCap": {
            "mcap_chg": 0.15, "turnover": 0.15, "hype": 0.35,
            "price": 0.15, "volume": 0.10, "volatility": 0.10
        }
    }.get(category_name, {
        "mcap_chg": 0.20, "turnover": 0.20, "hype": 0.30,
        "price": 0.10, "volume": 0.10, "volatility": 0.10
    })

    # Calculate raw scores for all tokens
    raw_scores = []
    for idx, token in enumerate(tokens):
        # Base score calculation using normalized values
        base_score = (
            weights["mcap_chg"] * mcap_analysis["normalized"][idx] +
            weights["turnover"] * turnover_analysis["normalized"][idx] +
            weights["hype"] * hype_analysis["normalized"][idx] +
            weights["price"] * price_analysis["normalized"][idx] +
            weights["volume"] * volume_analysis["normalized"][idx] +
            weights["volatility"] * volatility_analysis["normalized"][idx]
        )

        # Bonus points for being an outlier
        # *Can adjust outlier bonus sensitivity
        outlier_bonus = 0
        if token["Market Cap (Change 24h)"] in mcap_analysis["outliers"]:
            outlier_bonus += 0.10
        if token["Turnover"] in turnover_analysis["outliers"]:
            outlier_bonus += 0.07
        if token["Hype Activity"] in hype_analysis["outliers"]:
            outlier_bonus += 0.07

        # Bonus for high rank in multiple metrics (top 15%)
        rank_bonus = 0
        # *Can adjust this threshold
        top_rank_threshold = 0.85  # Top 15%
        if mcap_analysis["ranks"][idx] > top_rank_threshold:
            rank_bonus += 0.03
        if turnover_analysis["ranks"][idx] > top_rank_threshold:
            rank_bonus += 0.03
        if hype_analysis["ranks"][idx] > top_rank_threshold:
            rank_bonus += 0.03

        # Apply rank bonus with diminishing returns
        rank_bonus = min(0.10, rank_bonus)

        # Bonus for price-volume correlation
        correlation_bonus = 0.03 * token["Price-Volume Correlation"]

        # Adjust for volatility with more granular approach and market cap context
        volatility_modifier = 0
        volatility = token["Volatility"]

        # Adjust ideal volatility ranges based on market cap category
        if category_name == "largeCap":
            # Large caps: reward stability, penalize high volatility
            if 2 <= volatility <= 10:  # Ideal for large caps
                volatility_modifier += 0.05
            elif 10 < volatility <= 20:  # Acceptable
                volatility_modifier += 0.02
            elif 20 < volatility <= 40:  # High
                volatility_modifier -= 0.03
            elif volatility > 40:  # Extreme
                volatility_modifier -= 0.08
        elif category_name == "midCap":
            # Mid caps: moderate volatility is ideal
            if 3 <= volatility <= 15:  # Ideal for mid caps
                volatility_modifier += 0.05
            elif 15 < volatility <= 30:  # Acceptable
                volatility_modifier += 0.02
            elif 30 < volatility <= 50:  # High
                volatility_modifier -= 0.03
            elif volatility > 50:  # Extreme
                volatility_modifier -= 0.07
        elif category_name in ["smallCap", "microCap"]:
            # Small/micro caps: higher volatility is expected
            if 5 <= volatility <= 25:  # Ideal for small caps
                volatility_modifier += 0.05
            elif 25 < volatility <= 40:  # Acceptable
                volatility_modifier += 0.02
            elif 40 < volatility <= 60:  # High but common
                volatility_modifier -= 0.02
            elif volatility > 60:  # Extreme
                volatility_modifier -= 0.06
        else:
            # Default case
            if 5 <= volatility <= 20:  # Ideal range
                volatility_modifier += 0.03
            elif volatility > 50:  # Too volatile
                volatility_modifier -= 0.07

        # Combine all factors for raw score
        raw_score = base_score + outlier_bonus + rank_bonus + correlation_bonus + volatility_modifier

        # Store raw score and components for later normalization
        raw_scores.append({
            "idx": idx,
            "token": token,
            "raw_score": raw_score,
            "base_score": base_score,
            "outlier_bonus": outlier_bonus,
            "rank_bonus": rank_bonus,
            "correlation_bonus": correlation_bonus,
            "volatility_modifier": volatility_modifier,
            "is_outlier": (
                token["Market Cap (Change 24h)"] in mcap_analysis["outliers"] or
                token["Turnover"] in turnover_analysis["outliers"] or
                token["Hype Activity"] in hype_analysis["outliers"]
            )
        })

    # TODO===== TAHAP 5: NORMALISASI SKOR AKHIR =====
    if raw_scores:
        # Sort by raw score
        raw_scores.sort(key=lambda x: x["raw_score"], reverse=True)

        # Determine highest and lowest scores
        max_raw = raw_scores[0]["raw_score"]
        min_raw = raw_scores[-1]["raw_score"] if len(raw_scores) > 1 else 0
        score_range = max_raw - min_raw

        # *If range is too small, use sigmoid to expand for better differentiation
        if score_range < 0.3:
            for score_data in raw_scores:
                # Normalize to 0-1 first
                if score_range > 0:
                    norm_position = (score_data["raw_score"] - min_raw) / score_range
                else:
                    norm_position = 0.5  # Default if all scores are the same

                # Use modified sigmoid function for better distribution
                final_score = 1 / (1 + np.exp(-10 * (norm_position - 0.5)))

                # Adjust range to 0.2-0.95 to avoid too many 1.0 scores
                final_score = 0.2 + (final_score * 0.75)

                # Add bonus for top 3 outliers
                if score_data["is_outlier"] and raw_scores.index(score_data) < 3:
                    final_score = min(0.98, final_score + 0.05)

                # Save final score
                score_data["token"]["Early Momentum Score"] = final_score
        else:
            # *If range is already large enough, use rank-based normalization
            for i, score_data in enumerate(raw_scores):
                # Top tokens get fixed high scores
                if i == 0:  # Top token
                    final_score = 0.95
                elif i == 1:  # Second token
                    final_score = 0.92
                elif i == 2:  # Third token
                    final_score = 0.89
                elif i < len(raw_scores) * 0.1:  # Top 10%
                    final_score = 0.85 - (i * 0.01)
                else:
                    # Rest use rank-based normalization with upper limit
                    rank_position = i / len(raw_scores)
                    final_score = max(0.2, 0.8 - (rank_position * 0.6))

                # Save final score
                score_data["token"]["Early Momentum Score"] = final_score

        # TODO===== TAHAP 6: SIMPAN KOMPONEN SKOR DAN METADATA =====
        for score_data in raw_scores:
            token = score_data["token"]
            idx = score_data["idx"]

            # Save all score components
            token["MCAP Score"] = mcap_analysis["normalized"][idx]
            token["Turnover Score"] = turnover_analysis["normalized"][idx]
            token["Hype Score"] = hype_analysis["normalized"][idx]
            token["Price Score"] = price_analysis["normalized"][idx]
            token["Volume Score"] = volume_analysis["normalized"][idx]
            token["Volatility Score"] = volatility_analysis["normalized"][idx]
            
            # Tambahkan estimasi momentum duration menggunakan data 7d
            token["Momentum Duration"] = estimate_momentum_duration(token)
            
            # Tambahkan klasifikasi momentum berdasarkan durasi dan skor
            score = token["Early Momentum Score"]
            duration = token["Momentum Duration"]
            
            # Klasifikasi momentum berdasarkan kombinasi skor dan durasi
            if score >= 0.8:
                if duration <= 2:
                    token["Momentum Type"] = "New Strong"  # Momentum baru dan kuat
                else:
                    token["Momentum Type"] = "Established Strong"  # Momentum kuat berkelanjutan
            elif score >= 0.6:
                if duration <= 2:
                    token["Momentum Type"] = "New Moderate"  # Momentum baru moderat
                else:
                    token["Momentum Type"] = "Established Moderate"  # Momentum moderat berkelanjutan
            else:
                if duration <= 2:
                    token["Momentum Type"] = "Emerging"  # Momentum baru tapi lemah
                else:
                    token["Momentum Type"] = "Fading"  # Momentum yang melemah
            
            token["Base Score"] = score_data["base_score"]
            token["Outlier Bonus"] = score_data["outlier_bonus"]
            token["Rank Bonus"] = score_data["rank_bonus"]
            token["Raw Score"] = score_data["raw_score"]
            token["Is Outlier"] = score_data["is_outlier"]

            # Determine momentum strength category
            if score >= 0.8:
                token["Momentum Strength"] = "Very Strong"
            elif score >= 0.7:
                token["Momentum Strength"] = "Strong"
            elif score >= 0.5:
                token["Momentum Strength"] = "Moderate"
            elif score >= 0.3:
                token["Momentum Strength"] = "Weak"
            else:
                token["Momentum Strength"] = "Very Weak"

    # TODO===== TAHAP 7: FILTER DAN URUTKAN HASIL =====
    # Filter tokens with positive MCAP change and minimum momentum score
    min_score_threshold = 0.15  # Minimum score to be considered for early momentum
    filtered_tokens = [t for t in tokens if t["Market Cap (Change 24h)"] > 0 and t["Early Momentum Score"] >= min_score_threshold]

    # Sort by momentum score
    return sorted(filtered_tokens, key=lambda x: x["Early Momentum Score"], reverse=True)

def estimate_momentum_duration(token):
    """
    Estimasi durasi momentum berdasarkan perbandingan perubahan harga 24h vs 7d.
    
    Args:
        token (dict): Data token
        
    Returns:
        int: Estimasi durasi momentum dalam hari
    """
    # Ambil metrik perubahan harga
    price_change_24h = parse_float(token.get("Price Changes 24h", 0))
    price_change_7d = parse_float(token.get("Price Changes 7d", 0))
    
    # Jika salah satu data tidak tersedia atau nol, gunakan metrik lain
    if not price_change_24h or not price_change_7d:
        mcap_change = token.get("Market Cap (Change 24h)", 0)
        score = token.get("Early Momentum Score", 0)
        
        # Estimasi sederhana berdasarkan mcap_change
        if mcap_change > 20:
            return 1
        elif mcap_change > 10:
            return 2
        elif score > 0.8:
            return 2
        else:
            return 3
    
    # Jika keduanya tersedia, hitung rasio untuk estimasi durasi
    
    # Jika keduanya positif, bandingkan rasio
    if price_change_24h > 0 and price_change_7d > 0:
        # Rasio perubahan 24h terhadap 7d
        ratio = price_change_24h / price_change_7d
        
        if ratio > 0.9:  # 90% pergerakan terjadi dalam 24 jam terakhir
            return 1
        elif ratio > 0.7:  # 70% pergerakan terjadi dalam 24 jam terakhir
            return 2
        elif ratio > 0.5:  # 50% pergerakan terjadi dalam 24 jam terakhir
            return 3
        elif ratio > 0.3:  # 30% pergerakan terjadi dalam 24 jam terakhir
            return 5
        else:
            return 7
    
    # Jika 24h positif tapi 7d negatif, ini momentum baru yang membalik tren
    elif price_change_24h > 0 and price_change_7d <= 0:
        return 1  # Momentum sangat baru (reversal)
    
    # Jika 24h negatif tapi 7d positif, momentum sudah berakhir
    elif price_change_24h <= 0 and price_change_7d > 0:
        # Gunakan skor untuk menentukan apakah masih ada momentum
        score = token.get("Early Momentum Score", 0)
        if score > 0.7:
            return 6  # Masih ada momentum meski ada koreksi
        else:
            return 7  # Momentum mungkin sudah berakhir
    
    # Jika keduanya negatif, tidak ada momentum positif
    else:
        # Tetap berikan estimasi berdasarkan skor
        score = token.get("Early Momentum Score", 0)
        if score > 0.7:  # Skor tinggi meski harga turun
            return 3  # Mungkin ada faktor lain yang mendorong skor tinggi
        else:
            return 7



