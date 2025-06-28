# GEX-API Complete

这个仓库包含了你的完整 CBOE GEX 抓取脚本 (`gex_test.py`) 以及一个 FastAPI 接口，方便部署并实时提供 GEX 数据查询。

## 文件说明

- `gex_test.py`: 你的原始 GEX 抓取与 Telegram 推播脚本
- `api/main.py`: FastAPI 服务入口，通过调用 `gex_test.gex()` 返回结果

## 安装与运行

```bash
# 安装依赖
pip install -r requirements.txt

# 本地调试
uvicorn api.main:app --reload --port 8000

# 访问示例
curl "http://localhost:8000/api/gex?symbol=CRM"
```

## 部署

推荐使用 Render 或 Heroku:
- 启动命令: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- 确保保留 `TELEGRAM_TOKEN` 和 `CHAT_ID` 环境变量
