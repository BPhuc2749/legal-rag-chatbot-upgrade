import time

from app.services.retrieval_service import RetrievalService
from app.services.rerank_service import RerankService
from app.services.llm_service import LLMService

from app.prompt import TEMPLATE


class RAGService:
    def __init__(self):
        self.retriever = RetrievalService()
        self.reranker = RerankService()
        self.llm = LLMService()

    # =========================
    # Context builder
    # =========================
    def format_context(self, docs):
        return "\n\n".join(
            doc.page_content
            for doc in docs
        )

    # =========================
    # Extract source
    # =========================
    def extract_sources(self, docs):
        sources = []
        seen = set()

        for doc in docs:
            source = doc.metadata.get(
                "source",
                "Unknown"
            )

            page = (
                doc.metadata.get("page", 0)
                + 1
            )

            key = (source, page)

            if key not in seen:
                seen.add(key)

                sources.append({
                    "source": source,
                    "page": page,
                })

        return sources

    # =========================
    # Main RAG pipeline
    # =========================
    def ask(self, question: str, tracer=None):
        total_start = time.time()

        # =========================
        # 1. Retrieval
        # =========================
        retrieval_start = time.time()

        retrieved = self.retriever.retrieve(question)

        retrieval_time = (
            time.time()
            - retrieval_start
        )

        hybrid_results = retrieved["hybrid"]
        faiss_docs = retrieved["faiss"]
        bm25_docs = retrieved["bm25"]

        # Trace FAISS + BM25
        if tracer:
            tracer.hybrid_search(
                vector_results=[
                    {
                        "chunk_id": d.metadata.get(
                            "chunk_id"
                        ),
                        "preview": d.page_content[:200],
                    }
                    for d in faiss_docs
                ],
                bm25_results=[
                    {
                        "chunk_id": d.metadata.get(
                            "chunk_id"
                        ),
                        "preview": d.page_content[:200],
                    }
                    for d in bm25_docs
                ],
                latency_ms=int(
                    retrieval_time * 1000
                ),
            )

        # Trace merged hybrid result
        if tracer:
            tracer.retrieval(
                results=[
                    {
                        "chunk_id": item["chunk_id"],
                        "source": (
                            item["doc"]
                            .metadata.get("source")
                        ),
                        "page": (
                            item["doc"]
                            .metadata.get("page")
                        ),
                        "faiss_score": item["faiss_score"],
                        "bm25_score": item["bm25_score"],
                        "final_score": item["final_score"],
                        "preview": (
                            item["doc"]
                            .page_content[:200]
                        ),
                    }
                    for item in hybrid_results
                ],
                top_k=len(hybrid_results),
                latency_ms=int(
                    retrieval_time * 1000
                ),
            )

        # Convert to Documents
        retrieved_docs = [
            item["doc"]
            for item in hybrid_results
        ]

        # =========================
        # 2. Rerank
        # =========================
        rerank_start = time.time()

        reranked_docs = (
            self.reranker.rerank(
                question,
                retrieved_docs
            )
        )

        rerank_time = (
            time.time()
            - rerank_start
        )

        if tracer:
            tracer.rerank(
                input_docs=retrieved_docs,
                output_docs=reranked_docs,
                scores=[
                    doc.metadata.get(
                        "rerank_score"
                    )
                    for doc in reranked_docs
                ],
                latency_ms=int(
                    rerank_time * 1000
                ),
            )

        # =========================
        # 3. Prompt
        # =========================
        context = self.format_context(
            reranked_docs
        )

        prompt = TEMPLATE.format(
            context=context,
            question=question,
        )

        # =========================
        # 4. LLM
        # =========================
        llm_start = time.time()

        response = self.llm.generate(
            prompt
        )

        llm_time = (
            time.time()
            - llm_start
        )

        answer = response["text"]

        if tracer:
            tracer.llm_call(
                model=None,
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=int(
                    llm_time * 1000
                ),
            )

        # =========================
        # 5. Final answer
        # =========================
        if tracer:
            tracer.final_answer(
                answer
            )

        total_time = (
            time.time()
            - total_start
        )

        if tracer:
            tracer.summary(
                retrieval_count=len(
                    hybrid_results
                ),
                rerank_count=len(
                    reranked_docs
                ),
                total_latency_ms=int(
                    total_time * 1000
                ),
            )

        # =========================
        # API response
        # =========================
        return {
            "answer": answer,

            "sources": self.extract_sources(
                reranked_docs
            ),

            "metrics": {
                "retrieval_time": round(
                    retrieval_time,
                    3,
                ),

                "rerank_time": round(
                    rerank_time,
                    3,
                ),

                "llm_time": round(
                    llm_time,
                    3,
                ),

                "total_time": round(
                    total_time,
                    3,
                ),
            },
        }