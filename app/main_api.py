from fastapi import FastAPI

from app.utils.device import DEVICE
from app.api.route import router
from app.core.middleware import RequestContextMiddleware


print(f"--- Hệ thống sử dụng Model đã nạp: {DEVICE} ---")


app = FastAPI(
    title="Legal RAG ChatBot API",
    description="API kiểm thử Legal RAG với Middleware và Tracing",
    version="1.0.0",
)

# Đăng ký Middleware
app.add_middleware(RequestContextMiddleware)

# Đăng ký các API routes
app.include_router(router)