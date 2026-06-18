import os
import json
import unicodedata

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# =====================================================
# CONFIG
# =====================================================

DATASET_PATH = r"E:\PROJECT\Legal_RAG_ChatBot\evaluation\evaluation_dataset.json"

VECTORSTORES = {
    "BKAI": r"E:\PROJECT\Legal_RAG_ChatBot\vectorstore\faiss",
    "BGE_M3": r"E:\PROJECT\Legal_RAG_ChatBot\vectorstore_bge_m3\faiss",
}

EMBEDDINGS = {
    "BKAI": "bkai-foundation-models/vietnamese-bi-encoder",
    "BGE_M3": "BAAI/bge-m3",
}

TOP_K = 5

# =====================================================
# HELPER
# =====================================================

def normalize_text(text):
    if text is None:
        return ""

    text = unicodedata.normalize("NFC", str(text))
    return text.lower().strip()

# =====================================================
# LOAD DATASET
# =====================================================

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    dataset = json.load(f)

print(f"Loaded {len(dataset)} questions")

# =====================================================
# EVALUATION
# =====================================================

results = []

for embedding_name, embedding_model in EMBEDDINGS.items():

    print("\n" + "=" * 80)
    print(f"Evaluating: {embedding_name}")
    print("=" * 80)

    embeddings = HuggingFaceEmbeddings(
        model_name=embedding_model,
        model_kwargs={"device": "cuda"},
    )

    db = FAISS.load_local(
        VECTORSTORES[embedding_name],
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

        expected_doc = normalize_text(
            item["expected_doc"]
        )

        expected_section = normalize_text(
            item["expected_section"]
        )

        section_key = normalize_text(
            item["section_key"]
        )

        docs = retriever.invoke(question)

        # =================================================
        # DOC RECALL
        # =================================================

        retrieved_docs = []

        for d in docs:

            src = os.path.basename(
                d.metadata.get("source", "")
            )

            retrieved_docs.append(
                normalize_text(src)
            )

        if len(retrieved_docs) >= 1:

            if expected_doc == retrieved_docs[0]:
                doc_hit_1 += 1

        if expected_doc in retrieved_docs[:3]:
            doc_hit_3 += 1

        if expected_doc in retrieved_docs[:5]:
            doc_hit_5 += 1

        # =================================================
        # SECTION RECALL
        # =================================================

        section_found_1 = False
        section_found_3 = False
        section_found_5 = False

        for rank, d in enumerate(docs):

            content = normalize_text(
                d.page_content
            )

            match = (
                section_key in content
                or expected_section in content
            )

            if not match:
                continue

            if rank == 0:
                section_found_1 = True

            if rank < 3:
                section_found_3 = True

            if rank < 5:
                section_found_5 = True

        if section_found_1:
            sec_hit_1 += 1

        if section_found_3:
            sec_hit_3 += 1

        if section_found_5:
            sec_hit_5 += 1

        if not section_found_5:

            failed_cases.append(
                {
                    "question": question,
                    "expected_doc": expected_doc,
                    "expected_section": expected_section,
                    "section_key": section_key,
                }
            )

    result = {
        "embedding": embedding_name,

        "doc_r1": doc_hit_1 / total,
        "doc_r3": doc_hit_3 / total,
        "doc_r5": doc_hit_5 / total,

        "sec_r1": sec_hit_1 / total,
        "sec_r3": sec_hit_3 / total,
        "sec_r5": sec_hit_5 / total,

        "failed_cases": failed_cases,
    }

    results.append(result)

# =====================================================
# FINAL COMPARISON
# =====================================================

print("\n")
print("=" * 120)
print("EMBEDDING BENCHMARK")
print("=" * 120)

print(
    f"{'EMBEDDING':<15}"
    f"{'DOC@1':<10}"
    f"{'DOC@3':<10}"
    f"{'DOC@5':<10}"
    f"{'SEC@1':<10}"
    f"{'SEC@3':<10}"
    f"{'SEC@5':<10}"
)

for r in results:

    print(
        f"{r['embedding']:<15}"
        f"{r['doc_r1']*100:<10.2f}"
        f"{r['doc_r3']*100:<10.2f}"
        f"{r['doc_r5']*100:<10.2f}"
        f"{r['sec_r1']*100:<10.2f}"
        f"{r['sec_r3']*100:<10.2f}"
        f"{r['sec_r5']*100:<10.2f}"
    )

# =====================================================
# BEST EMBEDDING
# =====================================================

best_result = max(
    results,
    key=lambda x: x["sec_r5"]
)

print("\n")
print("=" * 120)
print("BEST EMBEDDING")
print("=" * 120)

print(best_result["embedding"])
print(f"Section Recall@5 = {best_result['sec_r5']*100:.2f}%")

# =====================================================
# FAILED CASES
# =====================================================

print("\n")
print("=" * 120)
print("FAILED SECTION CASES")
print("=" * 120)

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