import asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gex_test import gex

app = FastAPI(title="GEX API")

# CORS 設定，允許跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GET 版本 API
@app.get("/api/gex")
def get_gex(symbol: str = Query(..., description="股票代號，例如 AAPL")):
    try:
        result = asyncio.run(gex(symbol))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# POST 版本 API
class GEXRequest(BaseModel):
    symbol: str

@app.post("/api/gex")
def post_gex(request: GEXRequest):
    try:
        result = asyncio.run(gex(request.symbol))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
