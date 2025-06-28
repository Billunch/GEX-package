import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
from matplotlib.cm import get_cmap
from telegram import Bot
import asyncio
import os

# ====== Telegram Token 與 Chat ID ======
TELEGRAM_TOKEN = "7563006732:AAGoShMBFu3_UW3MFNhRQwoWQBRfdGJLrmY"
CHAT_ID = "5140400544"  # 例如 -123456789

# ====== GEX 分析主程式 ======
async def gex(stockid):
    async def send_telegram_message(message, image_path=None):
        try:
            bot = Bot(token=TELEGRAM_TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as photo:
                    await bot.send_photo(chat_id=CHAT_ID, photo=photo)
            print(f"✅ 已發送：{stockid}")
        except Exception as e:
            print(f"❌ 發送失敗 {stockid}：{e}")

    def is_valid_date(date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    # 取得 CBOE API
    api_url = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{stockid}.json"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        await send_telegram_message(f"<b>{stockid} 錯誤</b>：資料取得失敗\n{e}")
        return

    current_price = data["data"]["current_price"]
    options = data["data"]["options"]

    # 整理選擇權資料
    options_data = []
    for option in options:
        option_symbol = option["option"]
        try:
            strike = int(option_symbol[-8:]) / 1000
            option_type = "call" if "C" in option_symbol else "put"
            expiry = option_symbol[3:9]
            expiry_date = f"20{expiry[:2]}-{expiry[2:4]}-{expiry[4:6]}"

            gamma = option.get("gamma", 0)
            open_interest = option.get("open_interest", 0) or 0
            delta = option.get("delta", 0)
            iv = option.get("iv", 0)

            direction = 1 if option_type == "call" else -1
            gex = gamma * open_interest * 100 * direction

            options_data.append({
                "strike": strike,
                "option_type": option_type,
                "expiry": expiry_date,
                "gamma": gamma,
                "gex": gex,
                "open_interest": open_interest,
                "delta": delta,
                "iv": iv
            })
        except Exception as e:
            print(f"⚠️ 選擇權解析失敗：{option_symbol}, {e}")

    if not options_data:
        await send_telegram_message(f"<b>{stockid}</b> 無有效選擇權資料")
        return

    df = pd.DataFrame(options_data)

    # 檢查是否只有單邊資料
    if df["option_type"].nunique() == 1:
        only_type = df["option_type"].iloc[0]
        await send_telegram_message(f"<b>{stockid}</b> 僅有 {only_type.upper()} 選擇權，另一邊為空")

    gex_by_strike_expiry = df.groupby(["strike", "expiry"])["gex"].sum().reset_index()
    oi_by_strike = df.pivot_table(index="strike", columns="option_type", values="open_interest", aggfunc="sum").fillna(0)
    delta_by_strike = df.pivot_table(index="strike", columns="option_type", values="delta", aggfunc="mean").fillna(0)

    # Key Level 計算（含防呆）
    call_wall = oi_by_strike["call"].idxmax() if "call" in oi_by_strike.columns else "N/A"
    put_wall = oi_by_strike["put"].idxmax() if "put" in oi_by_strike.columns else "N/A"
    call_25_delta = delta_by_strike["call"].sub(0.25).abs().idxmin() if "call" in delta_by_strike.columns else "N/A"
    put_25_delta = delta_by_strike["put"].sub(-0.25).abs().idxmin() if "put" in delta_by_strike.columns else "N/A"

    # Implied Move 計算
    iv_by_expiry = df.groupby("expiry")["iv"].mean().to_dict()
    implied_moves = {}
    today = datetime.now().strftime("%Y-%m-%d")
    for expiry, iv in iv_by_expiry.items():
        if is_valid_date(expiry):
            days = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.strptime(today, "%Y-%m-%d")).days
            if iv > 0 and days > 0:
                move = current_price * iv * (days / 365) ** 0.5
                implied_moves[expiry] = move
        else:
            print(f"⚠️ 發現異常 expiry 格式：{expiry}，已跳過")

    # 訊息內容
    message = f"<b>{stockid} Options Analysis</b>\n"
    message += f"Current Price: {current_price}\n"

    if call_wall != "N/A":
        message += f"Call Wall: {call_wall} (OI: {oi_by_strike.loc[call_wall, 'call']:.0f})\n"
    else:
        message += "Call Wall: N/A\n"

    if put_wall != "N/A":
        message += f"Put Wall: {put_wall} (OI: {oi_by_strike.loc[put_wall, 'put']:.0f})\n"
    else:
        message += "Put Wall: N/A\n"

    message += f"Call 25 Delta: {call_25_delta}\n"
    message += f"Put 25 Delta: {put_25_delta}\n\n"
    message += "📈 <b>Implied Move</b>:\n"
    for expiry, move in implied_moves.items():
        lower = current_price - move
        upper = current_price + move
        message += f"{expiry}: ±{move:.2f} → {lower:.2f} ~ {upper:.2f}\n"

    # 繪圖
    plt.figure(figsize=(20, 10))
    cmap = get_cmap("tab10")
    expiries = sorted(df["expiry"].unique())
    colors = [cmap(i % 10) for i in range(len(expiries))]
    color_map = dict(zip(expiries, colors))

    for expiry in expiries:
        subset = gex_by_strike_expiry[gex_by_strike_expiry["expiry"] == expiry]
        plt.plot(subset["gex"], subset["strike"], label=f"Gamma {expiry}", color=color_map[expiry])

    for strike in sorted(df["strike"].unique()):
        sub = df[df["strike"] == strike]
        for expiry in expiries:
            call_oi = sub[(sub["option_type"] == "call") & (sub["expiry"] == expiry)]["open_interest"].sum()
            put_oi = sub[(sub["option_type"] == "put") & (sub["expiry"] == expiry)]["open_interest"].sum()
            if call_oi > 0:
                plt.barh(strike, call_oi, height=3, color=color_map[expiry], alpha=0.4)
            if put_oi > 0:
                plt.barh(strike, -put_oi, height=3, color=color_map[expiry], alpha=0.4)

    if isinstance(current_price, (float, int)):
        plt.axhline(y=current_price, color="black", linestyle="--", label=f"Price {current_price}")
    if call_wall != "N/A":
        plt.axhline(y=call_wall, color="orange", linestyle="--", label=f"Call Wall {call_wall}")
    if put_wall != "N/A":
        plt.axhline(y=put_wall, color="green", linestyle="--", label=f"Put Wall {put_wall}")
    if call_25_delta != "N/A":
        plt.axhline(y=call_25_delta, color="purple", linestyle=":", label=f"Call 25Δ {call_25_delta}")
    if put_25_delta != "N/A":
        plt.axhline(y=put_25_delta, color="cyan", linestyle=":", label=f"Put 25Δ {put_25_delta}")

    plt.xlabel("Dealer Gamma Exposure (GEX)")
    plt.ylabel("Strike Price")
    plt.title(f"{stockid} GEX Analysis")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True)
    plt.tight_layout()

    # 儲存與發送
    plot_path = f"{stockid}_gex.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    await send_telegram_message(message, plot_path)
    if os.path.exists(plot_path):
        os.remove(plot_path)

# ====== 股票清單與執行主函式 ======
stock_list = ["CRM", "NEE", "DFH", "ISRG", "OKLO","LNG", "LRN", "LLY", "IONQ"]

async def main():
    for stock in stock_list:
        await gex(stock)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
