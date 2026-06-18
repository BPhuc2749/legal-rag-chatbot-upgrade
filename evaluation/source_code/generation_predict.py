import os
import json
import time
import unicodedata
from typing import Any, Dict, List

from dotenv import load_dotenv
from tqdm import tqdm

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from app.config import VECTORSTORE_PATH, EMBED_MODEL, TEMPERATURE

# =========================
# LOAD ENV
# =========================
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")


TOP_K = 20


if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


# =========================
# PROMPT (PRODUCTION VERSION)
# =========================
TEMPLATE = """
Bạn là một trợ lý AI chuyên về luật và dữ liệu.

Chỉ sử dụng CONTEXT để trả lời.

Nếu không có thông tin: nói "Không tìm thấy thông tin trong tài liệu."

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

PROMPT = ChatPromptTemplate.from_template(TEMPLATE)


# =========================
# LEGAL RAG PIPELINE
# =========================
class LegalRAGPipeline:
    def __init__(self):
        # embedding
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cuda"},
        )

        # vectorstore
        self.db = FAISS.load_local(
            VECTORSTORE_PATH,
            self.embeddings,
            allow_dangerous_deserialization=True,
        )

        faiss_retriever = self.db.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": TOP_K,
                "fetch_k": 30,
                "lambda_mult": 0.8,
            },
        )

        all_docs = list(self.db.docstore._dict.values())

        bm25 = BM25Retriever.from_documents(all_docs)
        bm25.k = TOP_K

        # ensemble retriever
        self.retriever = EnsembleRetriever(
            retrievers=[faiss_retriever, bm25],
            weights=[0.7, 0.3],
        )

        # LLM (Google AI Studio)
        self.llm = ChatGoogleGenerativeAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
        )

        self.chain = PROMPT | self.llm | StrOutputParser()

    # =========================
    # UTIL
    # =========================
    def normalize_text(self, text: str) -> str:
        return unicodedata.normalize("NFC", text).lower()

    def classify_source(self, filename: str) -> str:
        name = self.normalize_text(filename)
        if "luật" in name:
            return "LUAT"
        if "chính sách" in name:
            return "CHINHSACH"
        return "QUYDINH"

    def format_docs(self, docs) -> str:
        out = []
        for d in docs:
            meta = d.metadata or {}
            src = meta.get("source", "unknown")
            page = meta.get("page", "")
            src_type = self.classify_source(src)

            out.append(
                f"[SOURCE_TYPE: {src_type} | SOURCE: {src} | PAGE: {page}]\n{d.page_content}"
            )

        return "\n\n---\n\n".join(out)

    def retrieve(self, question: str):
        return self.retriever.invoke(question)

    # =========================
    # RUN PIPELINE
    # =========================
    def run(self, question: str) -> Dict[str, Any]:
        start = time.time()

        docs = self.retrieve(question)
        context = self.format_docs(docs)

        answer = self.chain.invoke({
            "context": context,
            "question": question
        })

        latency = time.time() - start

        return {
            "answer": answer,
            "latency": latency,
        }


# =========================
# RATE LIMIT CONTROLLER
# =========================
class RateLimiter:
    def __init__(self, rpm=15):
        self.rpm = rpm
        self.interval = 60 / rpm
        self.last_call = 0

    def wait(self):
        now = time.time()
        diff = now - self.last_call

        if diff < self.interval:
            time.sleep(self.interval - diff)

        self.last_call = time.time()


# =========================
# MAIN BENCHMARK
# =========================
INPUT_PATH = r"E:\PROJECT\Legal_RAG_ChatBot\evaluation\evaluation_generation.json"
OUTPUT_PATH = "generation_predict.json"


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    rag = LegalRAGPipeline()
    limiter = RateLimiter(rpm=15)

    results = []

    print(f"Total: {len(dataset)} samples")

    for item in tqdm(dataset):
        question = item["question"]

        try:
            limiter.wait() 

            res = rag.run(question)

            item["predict"] = res["answer"]
            item["latency"] = res["latency"]

        except Exception as e:
            item["predict"] = f"ERROR: {str(e)}"
            item["latency"] = -1

        results.append(item)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\nDONE")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()