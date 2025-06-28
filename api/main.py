import asyncio
from fastapi import FastAPI, HTTPException, Query
from gex_test import gex  # your original async gex function

app = FastAPI(title="GEX Full API")

@app.get("/api/gex")
def get_gex(symbol: str = Query(..., description="股票代號")):
    try:
        # run async gex to get data dict
        result = asyncio.run(gex(symbol))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
