from sentence_transformers import CrossEncoder
from app.utils.device import DEVICE
from app.config import (
    RERANK_MODEL,
    RERANK_TOP_K
)


class RerankService:

    def __init__(self):
        self.reranker = CrossEncoder(
            RERANK_MODEL,
            device=DEVICE,
            cache_dir="/app/model_cache"
        )

    def rerank(
        self,
        question: str,
        docs,
        top_k: int = RERANK_TOP_K,
    ):
        if not docs:
            return []

        # tạo cặp (question, chunk)
        pairs = [
            (
                question,
                doc.page_content
            )
            for doc in docs
        ]

        scores = self.reranker.predict(
            pairs
        )

        ranked = sorted(
            zip(scores, docs),
            key=lambda x: x[0],
            reverse=True,
        )

        results = []

        for score, doc in ranked[:top_k]:

            # lưu score vào metadata để trace
            doc.metadata["rerank_score"] = float(score)

            results.append(doc)

        return results