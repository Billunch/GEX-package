import aiohttp
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

async def gex(symbol: str) -> dict:
    url = f"https://www.cboe.com/us/options/market_statistics/gamma_exposure/?symbol={symbol.upper()}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise ValueError(f"無法取得 CBOE 數據（HTTP {response.status}）")

            html = await response.text()

    # 假設你有處理 HTML -> DataFrame 的邏輯
    # 這裡提供範例 DataFrame
    data = {
        "strike": [100, 105, 110],
        "call_gex": [1.5, 2.3, 0.8],
        "put_gex": [-0.6, -1.0, -2.1]
    }
    df = pd.DataFrame(data)

    # 畫圖（可選）
    fig, ax = plt.subplots()
    ax.bar(df["strike"], df["call_gex"], label="Call GEX", alpha=0.7)
    ax.bar(df["strike"], df["put_gex"], label="Put GEX", alpha=0.7)
    ax.set_title(f"GEX 分布圖 - {symbol.upper()}")
    ax.legend()
    ax.set_xlabel("履約價")
    ax.set_ylabel("Gamma Exposure")

    # 轉為 base64 傳給前端或 API
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close()

    return {
        "symbol": symbol.upper(),
        "gex_data": df.to_dict(orient="records"),
        "chart_base64": image_base64
    }
