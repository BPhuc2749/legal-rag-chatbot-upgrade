import os
import json
import time
import random
import numpy as np
from tqdm import tqdm
from typing import List, Dict, Any

from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from sentence_transformers import CrossEncoder

from app.config import VECTORSTORE_PATH, EMBED_MODEL, TEMPERATURE


# =========================
# LOAD ENV
# =========================
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


# =========================
# EMBEDDING MODEL (fixed)
# =========================
embeddings = HuggingFaceEmbeddings(
    model_name=EMBED_MODEL,
    model_kwargs={"device": "cuda"},
)


# =========================
# LOAD VECTORSTORE
# =========================
db = FAISS.load_local(
    VECTORSTORE_PATH,
    embeddings,
    allow_dangerous_deserialization=True,
)

faiss_retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 20,
        "fetch_k": 30,
        "lambda_mult": 0.8,
    },
)

bm25 = BM25Retriever.from_documents(list(db.docstore._dict.values()))
bm25.k = 20

hybrid_retriever = EnsembleRetriever(
    retrievers=[faiss_retriever, bm25],
    weights=[0.7, 0.3],
)


# =========================
# RERANKER
# =========================
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cuda")


def rerank(question, docs, top_k=5):
    pairs = [(question, d.page_content) for d in docs]
    scores = reranker.predict(pairs)

    ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
    return [d for _, d in ranked[:top_k]]


# =========================
# LLM JUDGE (faithfulness)
# =========================
llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=0
)

def safe_llm_call(llm, prompt, sleep_time=5):
    """
    Gọi LLM an toàn, có sleep giữa các request để tránh rate limit
    """
    while True:
        try:
            response = llm.invoke(prompt)
            time.sleep(sleep_time)  # 👈 delay sau mỗi request
            return response
        except Exception as e:
            print(f"[WARN] Rate limit hit or error: {e}")
            print("Retry after 40s...")
            time.sleep(40)

import re

def parse_faithfulness_score(text):

    if isinstance(text, list):

        if len(text) == 0:
            return 0.0

        text = str(text[0])

    text = str(text).strip()

    match = re.search(
        r"(0(?:\.\d+)?|1(?:\.0+)?)",
        text
    )

    if match:
        return float(match.group(1))

    return 0.0

def faithfulness_judge(context: str, answer: str) -> float:
    prompt = f"""
Bạn là một hệ thống đánh giá rất nghiêm ngặt.

Bạn sẽ được cung cấp:
- CONTEXT (ngữ cảnh từ tài liệu)
- ANSWER (câu trả lời do hệ thống tạo ra)

Nhiệm vụ:
- Kiểm tra từng ý (claim) trong ANSWER có được hỗ trợ trực tiếp bởi CONTEXT hay không.
- Nếu một ý không có trong CONTEXT hoặc suy diễn vượt quá CONTEXT thì xem là KHÔNG được hỗ trợ.

Quy tắc chấm điểm:
- Trả về DUY NHẤT một số thực trong khoảng từ 0 đến 1.
- 0 = hoàn toàn không dựa trên CONTEXT (hallucination)
- 1 = tất cả các ý trong ANSWER đều được CONTEXT hỗ trợ đầy đủ

Không giải thích, không thêm text.

CONTEXT:
{context}

ANSWER:
{answer}

SCORE:
"""
    res = safe_llm_call(llm, prompt, sleep_time=5)
    return parse_faithfulness_score(res.content)


# =========================
# EMBEDDING SIMILARITY
# =========================
def semantic_score(a: str, b: str) -> float:
    emb = embeddings.embed_documents([a, b])
    return float(cosine_similarity([emb[0]], [emb[1]])[0][0])


# =========================
# CONTEXT FORMAT
# =========================
def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])


# =========================
# PIPELINE FOR FAITHFULNESS
# =========================
def retrieve_context(question: str):
    docs = hybrid_retriever.invoke(question)
    docs = rerank(question, docs, top_k=5)
    return docs


# =========================
# MAIN EVAL
# =========================
DATA_PATH = r"E:\PROJECT\Legal_RAG_ChatBot\evaluation\generation_predict.json"
OUTPUT_PATH = r"E:\PROJECT\Legal_RAG_ChatBot\evaluation\evaluation_result.json"


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []

    semantic_scores = []
    faith_scores = []
    latencies = []
    # =========================
    # BREAKDOWN
    # =========================
    difficulty_semantic = {}
    difficulty_faith = {}

    type_semantic = {}
    type_faith = {}
    for item in tqdm(data):

        question = item["question"]
        ground_truth = item["ground_truth"]
        predict = item["predict"]

        # =========================
        # (1) SEMANTIC
        # =========================
        sem = semantic_score(predict, ground_truth)

        # =========================
        # (2) FAITHFULNESS
        # =========================
        docs = retrieve_context(question)
        context = format_docs(docs)

        faith = faithfulness_judge(context, predict)

        semantic_scores.append(sem)
        faith_scores.append(faith)

        difficulty = item.get("difficulty", "unknown")
        answer_type = item.get("answer_type", "unknown")

        difficulty_semantic.setdefault(
            difficulty,
            []
        ).append(sem)

        difficulty_faith.setdefault(
            difficulty,
            []
        ).append(faith)

        type_semantic.setdefault(
            answer_type,
            []
        ).append(sem)

        type_faith.setdefault(
            answer_type,
            []
        ).append(faith)
        
        results.append({
            **item,
            "semantic": sem,
            "faithfulness": faith,
        })

    difficulty_report = {}

    for k in difficulty_semantic:
        difficulty_report[k] = {
            "semantic": float(
                np.mean(difficulty_semantic[k])
            ),
            "faithfulness": float(
                np.mean(difficulty_faith[k])
            ),
            "count": len(
                difficulty_semantic[k]
            )
        }

    type_report = {}

    for k in type_semantic:
        type_report[k] = {
            "semantic": float(
                np.mean(type_semantic[k])
            ),
            "faithfulness": float(
                np.mean(type_faith[k])
            ),
            "count": len(
                type_semantic[k]
            )
        }
    error_count = sum(
    1
    for x in data
    if str(
        x.get("predict", "")
    ).startswith("ERROR")
    )
    
    valid_latencies = [
    x["latency"]
    for x in data
    if x.get("latency", -1) > 0
    ]
    # =========================
    # SUMMARY
    # =========================
    report = {

    "num_samples": len(data),

    "error_count": error_count,

    "semantic": float(
        np.mean(semantic_scores)
    ),

    "faithfulness": float(
        np.mean(faith_scores)
    ),

    "latency": {
        "avg": float(
            np.mean(valid_latencies)
        ),
        "min": float(
            np.min(valid_latencies)
        ),
        "max": float(
            np.max(valid_latencies)
        )
    },

    "difficulty": difficulty_report,

    "answer_type": type_report,
    }

    print("\n================ RESULTS ================")

    print(
        "Samples:",
        report["num_samples"]
    )

    print(
        "Errors:",
        report["error_count"]
    )

    print(
        "Semantic:",
        report["semantic"]
    )

    print(
        "Faithfulness:",
        report["faithfulness"]
    )

    print(
        "Latency Avg:",
        report["latency"]["avg"]
    )

    print(
        "Latency Min:",
        report["latency"]["min"]
    )

    print(
        "Latency Max:",
        report["latency"]["max"]
    )

    print("\n===== DIFFICULTY =====")

    for k, v in difficulty_report.items():

        print(
            f"{k:<10}"
            f"Count={v['count']:<3} "
            f"Semantic={v['semantic']:.4f} "
            f"Faithfulness={v['faithfulness']:.4f}"
        )

    print("\n===== ANSWER TYPE =====")

    for k, v in type_report.items():

        print(
            f"{k:<12}"
            f"Count={v['count']:<3} "
            f"Semantic={v['semantic']:.4f} "
            f"Faithfulness={v['faithfulness']:.4f}"
        )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "report": report,
            "details": results
        }, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()