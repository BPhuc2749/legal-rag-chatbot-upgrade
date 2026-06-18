from typing import Any, Dict, List, Optional
from app.core.logging import log_event
from app.core.context import get_request_id, get_query


class RAGTracer:
    def __init__(self):
        pass

    # =========================
    # SAFE CONTEXT SNAPSHOT
    # =========================
    def _base(self) -> Dict[str, Any]:
        return {
            "request_id": get_request_id() or "unknown",
            "query": get_query() or "unknown",
        }

    # =========================
    # SAFE SERIALIZER
    # =========================
    def _safe(self, data: Any) -> Any:
        """
        Convert non-serializable objects to string fallback
        """
        if isinstance(data, (str, int, float, bool)) or data is None:
            return data

        if isinstance(data, list):
            return [self._safe(x) for x in data]

        if isinstance(data, dict):
            return {k: self._safe(v) for k, v in data.items()}

        return str(data)

    # =========================
    # RETRIEVAL
    # =========================
    def retrieval(
        self,
        results: List[Dict[str, Any]],
        top_k: int,
        latency_ms: Optional[int] = None
    ):
        log_event({
            "event": "retrieval",
            **self._base(),
            "top_k": top_k,
            "results": self._safe(results),
            "latency_ms": latency_ms,
        })

    # =========================
    # HYBRID SEARCH
    # =========================
    def hybrid_search(
        self,
        bm25_results: List[Any],
        vector_results: List[Any],
        latency_ms: Optional[int] = None
    ):
        log_event({
            "event": "hybrid_search",
            **self._base(),
            "bm25_hits": self._safe(bm25_results),
            "vector_hits": self._safe(vector_results),
            "latency_ms": latency_ms,
        })

    # =========================
    # RERANK
    # =========================
    def rerank(
        self,
        input_docs: List[Any],
        output_docs: List[Any],
        scores: List[float],
        latency_ms: Optional[int] = None
    ):
        log_event({
            "event": "rerank",
            **self._base(),
            "input_count": len(input_docs),
            "output_count": len(output_docs),
            "scores": scores,
            "latency_ms": latency_ms,
        })

    # =========================
    # LLM CALL
    # =========================
    def llm_call(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: Optional[str] = None,
        latency_ms: Optional[int] = None
    ):
        log_event({
            "event": "llm_call",
            **self._base(),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency_ms": latency_ms,
        })

    # =========================
    # FINAL ANSWER
    # =========================
    def final_answer(self, answer: str):
        log_event({
            "event": "final_answer",
            **self._base(),
            "answer": answer,
        })

    # =========================
    # PIPELINE SUMMARY
    # =========================
    def summary(
        self,
        retrieval_count: int,
        rerank_count: int,
        total_latency_ms: int,
    ):
        log_event({
            "event": "trace_summary",
            **self._base(),
            "retrieval_count": retrieval_count,
            "rerank_count": rerank_count,
            "total_latency_ms": total_latency_ms,
        })