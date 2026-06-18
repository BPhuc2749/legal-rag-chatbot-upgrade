import os
import json
import re
import unicodedata

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.config import EMBED_MODEL

# =====================================================
# CONFIG
# =====================================================

DATASET_PATH = r"E:\PROJECT\Legal_RAG_ChatBot\evaluation\evaluation_dataset.json"

VECTORSTORES = {
    "800_200": r"E:\PROJECT\Legal_RAG_ChatBot\vectorstore_800_200\faiss",
    "1000_250": r"E:\PROJECT\Legal_RAG_ChatBot\vectorstore_1000_250\faiss",
    "1250_500": r"E:\PROJECT\Legal_RAG_ChatBot\vectorstore\faiss",
}

TOP_K = 5

# =====================================================
# NORMALIZE
# =====================================================

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# =====================================================
# LOAD DATASET
# =====================================================

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    dataset = json.load(f)

print(f"\nLoaded {len(dataset)} questions")

# =====================================================
# EMBEDDING
# =====================================================

embeddings = HuggingFaceEmbeddings(
    model_name=EMBED_MODEL,
    model_kwargs={"device": "cuda"},
)

# =====================================================
# EVALUATE
# =====================================================

def evaluate_vectorstore(name, vectorstore_path):

    print("\n" + "=" * 80)
    print(f"Evaluating: {name}")
    print("=" * 80)

    db = FAISS.load_local(
        vectorstore_path,
        embeddings,
        allow_dangerous_deserialization=True,
    )

    retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": TOP_K,
            "fetch_k": 20,
            "lambda_mult": 0.8,
        },
    )

    total = len(dataset)

    doc_hit_1 = 0
    doc_hit_3 = 0
    doc_hit_5 = 0

    sec_hit_1 = 0
    sec_hit_3 = 0
    sec_hit_5 = 0

    failed_cases = []

    for item in dataset:

        question = item["question"]

        expected_doc = item["expected_doc"]

        expected_section = normalize_text(
            item["expected_section"]
        )
        section_key = normalize_text(
            item["section_key"]
        )

        docs = retriever.invoke(question)

        # ======================================
        # DOCUMENT RECALL
        # ======================================

        retrieved_docs = []

        for d in docs:

            src = os.path.basename(
                d.metadata.get("source", "")
            )

            retrieved_docs.append(src)

        if expected_doc in retrieved_docs[:1]:
            doc_hit_1 += 1

        if expected_doc in retrieved_docs[:3]:
            doc_hit_3 += 1

        if expected_doc in retrieved_docs[:5]:
            doc_hit_5 += 1

        # ======================================
        # SECTION RECALL
        # ======================================

        top1_hit = False
        top3_hit = False
        top5_hit = False

        for idx, d in enumerate(docs):

            content = normalize_text(
                d.page_content
            )

            if (section_key in content or expected_section in content):

                if idx < 1:
                    top1_hit = True

                if idx < 3:
                    top3_hit = True

                if idx < 5:
                    top5_hit = True

        if top1_hit:
            sec_hit_1 += 1

        if top3_hit:
            sec_hit_3 += 1

        if top5_hit:
            sec_hit_5 += 1

        # ======================================
        # FAILED CASES
        # ======================================

        if not top5_hit:

            failed_cases.append(
                {
                    "question": question,
                    "expected_doc": expected_doc,
                    "expected_section": expected_section,
                    "section_key": section_key,
                }
            )

    result = {
        "config": name,

        "doc_r1": doc_hit_1 / total,
        "doc_r3": doc_hit_3 / total,
        "doc_r5": doc_hit_5 / total,

        "sec_r1": sec_hit_1 / total,
        "sec_r3": sec_hit_3 / total,
        "sec_r5": sec_hit_5 / total,

        "failed": len(failed_cases),

        "failed_cases": failed_cases
    }

    print(
        f"Document Recall@1 : {result['doc_r1']:.2%}"
    )
    print(
        f"Document Recall@3 : {result['doc_r3']:.2%}"
    )
    print(
        f"Document Recall@5 : {result['doc_r5']:.2%}"
    )

    print()

    print(
        f"Section Recall@1  : {result['sec_r1']:.2%}"
    )
    print(
        f"Section Recall@3  : {result['sec_r3']:.2%}"
    )
    print(
        f"Section Recall@5  : {result['sec_r5']:.2%}"
    )

    print()
    print(f"Failed Cases      : {len(failed_cases)}")

    return result

# =====================================================
# RUN
# =====================================================

results = []

for config_name, path in VECTORSTORES.items():

    result = evaluate_vectorstore(
        config_name,
        path,
    )

    results.append(result)

# =====================================================
# SUMMARY
# =====================================================

print("\n")
print("=" * 120)
print("FINAL COMPARISON")
print("=" * 120)

header = (
    f"{'CONFIG':<15}"
    f"{'DOC@1':<10}"
    f"{'DOC@3':<10}"
    f"{'DOC@5':<10}"
    f"{'SEC@1':<10}"
    f"{'SEC@3':<10}"
    f"{'SEC@5':<10}"
)

print(header)

for r in results:

    print(
        f"{r['config']:<15}"
        f"{r['doc_r1']:<10.2%}"
        f"{r['doc_r3']:<10.2%}"
        f"{r['doc_r5']:<10.2%}"
        f"{r['sec_r1']:<10.2%}"
        f"{r['sec_r3']:<10.2%}"
        f"{r['sec_r5']:<10.2%}"
    )

best = max(
    results,
    key=lambda x: x["sec_r5"]
)

print("\n")
print("=" * 120)
print("BEST CONFIG")
print("=" * 120)

print(best["config"])
print(
    f"Section Recall@5 = {best['sec_r5']:.2%}"
)


results = []

for config_name, path in VECTORSTORES.items():

    result = evaluate_vectorstore(
        config_name,
        path,
    )

    results.append(result)
    
print("\n")
print("=" * 120)
print("FAILED SECTION CASES")
print("=" * 120)

best_result = max(
    results,
    key=lambda x: x["sec_r5"]
)

for case in best_result["failed_cases"][:10]:

    print("\n" + "=" * 80)

    print("QUESTION:")
    print(case["question"])

    print("\nEXPECTED DOC:")
    print(case["expected_doc"])

    print("\nEXPECTED SECTION:")
    print(case["expected_section"])

    print("\nSECTION KEY:")
    print(case["section_key"])