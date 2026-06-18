# --- FIX LỖI HfFolder (Giữ nguyên) ---
import sys
try:
    from huggingface_hub import HfFolder
except ImportError:
    class MockHfFolder:
        @staticmethod
        def get_token(): return None
        @staticmethod
        def save_token(token): pass
        @staticmethod
        def delete_token(): pass
    import huggingface_hub
    huggingface_hub.HfFolder = MockHfFolder
    sys.modules["huggingface_hub.HfFolder"] = MockHfFolder
# ------------------------------------------

import uuid
from fastapi import FastAPI
import gradio as gr
from app.utils.device import DEVICE
from app.api.route import router, rag 
from app.core.middleware import RequestContextMiddleware

# IMPORT THÊM CÁC CÔNG CỤ LOGGING
from app.core.tracer import RAGTracer
from app.core.context import set_request_id, set_query

print(f"--- Hệ thống sử dụng Model đã nạp từ Route trên: {DEVICE} ---")

app = FastAPI(title="Legal RAG ChatBot")
app.add_middleware(RequestContextMiddleware)
app.include_router(router)

# ĐỊNH NGHĨA GIAO DIỆN CHAT
def legal_chat_logic(message, history):
    try:
        # 1. Khởi tạo Context thủ công cho Gradio (Vì không đi qua Middleware)
        req_id = f"gradio-{uuid.uuid4()}"
        set_request_id(req_id)
        set_query(message)

        # 2. Khởi tạo Tracer
        tracer = RAGTracer()

        # 3. TRUYỀN TRACER VÀO HÀM ASK (Quan trọng nhất)
        result = rag.ask(message, tracer=tracer) 
        
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        metrics = result.get("metrics", {})
        
        response = f"{answer}\n\n---"
        if sources:
            response += "\n\n**Nguồn trích dẫn:**"
            for i, s in enumerate(sources, 1):
                response += f"\n{i}. *{s['source']}* (Trang {s['page']})"
        
        response += f"\n\n*(⚡ Phản hồi trong {metrics.get('total_time', 0)}s)*"
        return response
    except Exception as e:
        return f"Lỗi: {str(e)}"

demo = gr.ChatInterface(
    fn=legal_chat_logic,
    title="⚖️ Trợ Lý Luật Cộng Nghệ AI",
    description="Hệ thống hỏi đáp dựa trên cơ sở dữ liệu luật CNTT liên quan đến dữ liệu, an ninh mạng, giao dịch điện tử",
    fill_height=True,
    examples=["Dữ liệu cá nhân là gì?","Quyền chủ thể dữ liệu là gì?","Giao dịch điện tử là gì?"],
    textbox=gr.Textbox(placeholder="Nhập câu hỏi của bạn...", container=False, scale=7)
)

app = gr.mount_gradio_app(app, demo, path="/")