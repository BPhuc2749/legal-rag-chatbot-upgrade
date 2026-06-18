FROM python:3.10-slim

WORKDIR /app

# Biến môi trường chuẩn
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CUDA_VISIBLE_DEVICES="" \
    DEVICE="cpu" \
    HF_HOME="/app/model_cache"

# Cài đặt system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel

# 🔥 Cài Torch CPU (Tiết kiệm dung lượng)
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Cài đặt requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Tạo các thư mục cần thiết trước khi tải model
RUN mkdir -p /app/model_cache /app/logs /app/vectorstore

# 🔥 TẢI MODEL NGAY LÚC BUILD (Bake-in)
# Đã sửa cache_dir thành cache_folder cho bản mới
RUN python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='bkai-foundation-models/vietnamese-bi-encoder', cache_folder='/app/model_cache')"
RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('BAAI/bge-reranker-v2-m3', cache_folder='/app/model_cache')"

# Copy code vào sau cùng để tận dụng cache
COPY app/ app/
COPY vectorstore/ vectorstore/

# Hugging Face yêu cầu port 7860
EXPOSE 7860

# Chạy Uvicorn với port 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]