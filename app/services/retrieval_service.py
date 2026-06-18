from typing import Dict, List, Any
from app.utils.device import DEVICE
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from app.config import (
    EMBED_MODEL,
    VECTORSTORE_PATH,
    FAISS_WEIGHT,
    BM25_WEIGHT,
    TOP_K,
)


class RetrievalService:
    def __init__(self):
        # Embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": DEVICE},
            cache_folder="/app/model_cache"
        )

        # Load FAISS index
        self.db = FAISS.load_local(
            VECTORSTORE_PATH,
            self.embeddings,
            allow_dangerous_deserialization=True,
        )

        # Vector retrieval
        self.faiss_retriever = self.db.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": TOP_K,
                "fetch": 30,
                "lambda_mult": 0.8,
            },
        )

        # Load all docs for BM25
        all_docs = list(self.db.docstore._dict.values())

        self.bm25 = BM25Retriever.from_documents(all_docs)
        self.bm25.k = TOP_K

    def retrieve(self, question: str) -> Dict[str, Any]:
        """
        Return full hybrid search information:
        {
            hybrid: merged results with scores,
            faiss: raw FAISS documents,
            bm25: raw BM25 documents
        }
        """

        # 1. Vector search
        faiss_docs = self.faiss_retriever.invoke(question)

        # 2. Keyword search
        bm25_docs = self.bm25.invoke(question)

        # 3. Merge by chunk_id
        hybrid_results = self._merge(
            faiss_docs,
            bm25_docs
        )

        return {
            "hybrid": hybrid_results,
            "faiss": faiss_docs,
            "bm25": bm25_docs,
        }

    def _merge(
        self,
        faiss_docs: List[Document],
        bm25_docs: List[Document],
    ) -> List[Dict[str, Any]]:

        merged = {}

        # =========================
        # FAISS contribution
        # =========================
        for rank, doc in enumerate(faiss_docs):
            chunk_id = doc.metadata.get("chunk_id")

            if chunk_id is None:
                continue

            score = FAISS_WEIGHT * (1 / (rank + 1))

            if chunk_id not in merged:
                merged[chunk_id] = {
                    "doc": doc,
                    "faiss_score": 0.0,
                    "bm25_score": 0.0,
                }

            merged[chunk_id]["faiss_score"] += score

        # =========================
        # BM25 contribution
        # =========================
        for rank, doc in enumerate(bm25_docs):
            chunk_id = doc.metadata.get("chunk_id")

            if chunk_id is None:
                continue

            score = BM25_WEIGHT * (1 / (rank + 1))

            if chunk_id not in merged:
                merged[chunk_id] = {
                    "doc": doc,
                    "faiss_score": 0.0,
                    "bm25_score": 0.0,
                }

            merged[chunk_id]["bm25_score"] += score

        # =========================
        # Calculate final score
        # =========================
        results = []

        for chunk_id, data in merged.items():

            final_score = (
                data["faiss_score"]
                + data["bm25_score"]
            )

            results.append({
                "doc": data["doc"],
                "chunk_id": chunk_id,
                "faiss_score": round(data["faiss_score"], 4),
                "bm25_score": round(data["bm25_score"], 4),
                "final_score": round(final_score, 4),
            })

        # =========================
        # Sort by final score
        # =========================
        results.sort(
            key=lambda x: x["final_score"],
            reverse=True,
        )

        return results