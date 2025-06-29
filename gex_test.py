import io
import requests
import pandas as pd
import matplotlib.pyplot as plt
import base64

async def gex(symbol: str):
    try:
        # CBOE 延遲選擇權資料 API
        api_url = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.json"
        response = requests.get(api_url)

        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}", "message": response.text}

        data = response.json()
        options = data.get("data", {}).get("options", [])
        if not options:
            return {"error": "找不到 options 資料", "raw": data}

        df = pd.DataFrame(options)
        if "strike_price" not in df.columns or "option_type" not in df.columns:
            return {"error": "資料格式錯誤", "columns": df.columns.tolist()}

        # 分 Call / Put
        call_df = df[df["option_type"] == "call"]
        put_df = df[df["option_type"] == "put"]

        # 畫圖
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(call_df["strike_price"], call_df["volume"], label="Call", marker="o")
        ax.plot(put_df["strike_price"], put_df["volume"], label="Put", marker="x")
        ax.set_title(f"{symbol.upper()} Call/Put Volume by Strike")
        ax.set_xlabel("Strike Price")
        ax.set_ylabel("Volume")
        ax.legend()
        ax.grid(True)

        # base64 輸出圖
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close(fig)

        return {
            "symbol": symbol.upper(),
            "chart_base64": image_base64,
            "note": "成功取得資料與圖表"
        }

    except Exception as e:
        return {"error": str(e)}
