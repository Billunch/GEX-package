import asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gex_test import gex  # 你的原始 async gex function

app = FastAPI(title="GEX Full API")

# ✅ 加入 CORS 中介層，讓 TypingMind 可以跨域呼叫 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 可改成指定來源網址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ GET 版本：支援 ?symbol=XXX 查詢
@app.get("/api/gex")
def get_gex(symbol: str = Query(..., description="股票代號，例如 AAPL")):
    try:
        result = asyncio.run(gex(symbol))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ POST 版本：支援 TypingMind Plugin 用 JSON 傳入
class GEXRequest(BaseModel):
    symbol: str

@app.post("/api/gex")
def post_gex(request: GEXRequest):
    try:
        result = asyncio.run(gex(request.symbol))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
