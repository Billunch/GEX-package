import requests
import pandas as pd
import numpy as np

def calculate_implied_move(df):
    # 簡單版本：用 ATM IV 粗估
    try:
        atm_row = df.iloc[(df['strike'] - df['underlying_price']).abs().argsort()[:1]]
        atm_iv = atm_row['iv'].values[0] / 100  # IV 為百分比
        days_to_exp = atm_row['days_to_expiration'].values[0]
        implied_move = atm_iv * np.sqrt(days_to_exp / 365) * atm_row['underlying_price'].values[0]
        return round(implied_move, 2)
    except Exception:
        return None

def calculate_gamma_exposure(df):
    try:
        df['GEX'] = df['gamma'] * df['open_interest'] * 100 * df['underlying_price']
        gex_by_strike = df.groupby('strike')['GEX'].sum().reset_index()
        gex_by_strike = gex_by_strike.sort_values('strike').to_dict(orient='records')
        return gex_by_strike
    except Exception:
        return []

async def gex(symbol: str):
    try:
        api_url = f"https://cdn.cboe.com/api/global/delayed_quotes/options_summary/{symbol.upper()}.json"
        response = requests.get(api_url)
        if response.status_code != 200:
            return {"error": f"API 回傳失敗，狀態碼: {response.status_code}", "url": api_url}

        raw_data = response.json()
        if "data" not in raw_data:
            return {"error": "API 回傳格式錯誤，缺少 'data' 欄位"}

        df = pd.DataFrame(raw_data["data"])
        if df.empty:
            return {"error": "無選擇權資料", "symbol": symbol}

        # 處理必要欄位
        required_columns = {"strike", "gamma", "open_interest", "iv", "underlying_price", "days_to_expiration"}
        missing = required_columns - set(df.columns)
        if missing:
            return {"error": "資料缺少必要欄位", "missing": list(missing)}

        implied_move = calculate_implied_move(df)
        gex_by_strike = calculate_gamma_exposure(df)

        return {
            "symbol": symbol.upper(),
            "implied_move": implied_move,
            "gex_by_strike": gex_by_strike,
            "raw_row_count": len(df),
        }

    except Exception as e:
        return {"error": str(e), "symbol": symbol}
