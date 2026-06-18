import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

VECTORSTORE_PATH = "vectorstore/faiss"
EMBED_MODEL = "bkai-foundation-models/vietnamese-bi-encoder"
TOP_K = 10

LLM_MODEL = "gemini-3.1-flash-lite"
TEMPERATURE = 0.1
FAISS_WEIGHT = 0.7
BM25_WEIGHT = 0.3
RERANK_TOP_K = 5
RERANK_MODEL = ("BAAI/bge-reranker-v2-m3")