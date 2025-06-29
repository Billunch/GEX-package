import io
import requests
import pandas as pd
import matplotlib.pyplot as plt
import base64

async def gex(symbol: str):
    try:
        # 建立 CBOE 查詢 URL
        api_url = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.json"
        response = requests.get(api_url)

        # 偵錯輸出
        print("Status code:", response.status_code)
        print("Response text:", response.text[:500])  # 前 500 字避免太長

        # 錯誤處理
        if response.status_code != 200:
            return {"error": f"CBOE API 回傳狀態碼: {response.status_code}", "body": response.text}

        data = response.json()

        # 假設我們取出 Call/Put 數量與價格資料
        options = data.get("data", {}).get("options", [])
        if not options:
            return {"error": "無法取得選擇權資料", "raw": data}

        df = pd.DataFrame(options)
        if df.empty or "strike_price" not in df.columns or "option_type" not in df.columns:
            return {"error": "CBOE 回傳格式錯誤", "columns": df.columns.tolist(), "raw": data}

        # 過濾 Call 與 Put 數據
        call_df = df[df["option_type"] == "call"]
        put_df = df[df["option_type"] == "put"]

        # 畫圖
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(call_df["strike_price"], call_df["volume"], label="Call", marker="o")
        ax.plot(put_df["strike_price"], put_df["volume"], label="Put", marker="x")
        ax.set_title(f"{symbol} Call/Put Volume by Strike Price")
        ax.set_xlabel("Strike Price")
        ax.set_ylabel("Volume")
        ax.legend()
        ax.grid(True)

        # 儲存為 base64 圖片
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close(fig)

        return {
            "symbol": symbol.upper(),
            "status": "success",
            "chart_base64": image_base64,
            "note": "成功取得資料與圖表"
        }

    except Exception as e:
        return {
            "error": str(e),
            "hint": "請確認 symbol 是否正確，或 CBOE 是否變更 API 結構",
        }
