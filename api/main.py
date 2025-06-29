from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gex_test import gex  # 你的 async gex function

app = FastAPI(title="GEX Full API")

# ✅ CORS 中介層
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 可視需求限制來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ GET API：支援 URL 查詢 ?symbol=xxx
@app.get("/api/gex")
async def get_gex(symbol: str = Query(..., description="股票代號，例如 AAPL")):
    try:
        result = await gex(symbol)
        if not result:
            raise HTTPException(status_code=404, detail=f"No GEX data found for {symbol}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GEX API error: {str(e)}")

# ✅ POST API：支援 JSON body，例如 {"symbol": "AAPL"}
class GEXRequest(BaseModel):
    symbol: str

@app.post("/api/gex")
async def post_gex(request: GEXRequest):
    try:
        result = await gex(request.symbol)
        if not result:
            raise HTTPException(status_code=404, detail=f"No GEX data found for {request.symbol}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GEX API error: {str(e)}")
