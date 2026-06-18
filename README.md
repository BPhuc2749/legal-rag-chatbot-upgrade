# Legal RAG Chatbot - Hệ thống hỏi đáp pháp luật sử dụng AI


## Demo trực tuyến

Người dùng có thể trải nghiệm trực tiếp hệ thống tại:

🔗 Hugging Face Space:
https://huggingface.co/spaces/BPhuc/legal-rag-chatbot-upgrade

**Lưu ý:**
- Demo được triển khai trên môi trường CPU miễn phí của Hugging Face Spaces.
- Thời gian phản hồi có thể chậm hơn so với môi trường GPU.
- Hệ thống có thể mất một khoảng thời gian để khởi động lại nếu Space ở trạng thái Sleep.

---


## 1. Giới thiệu dự án

Legal RAG Chatbot là hệ thống hỏi đáp pháp luật sử dụng kiến trúc **Retrieval-Augmented Generation (RAG)** nhằm hỗ trợ tra cứu các văn bản pháp luật Việt Nam liên quan đến:

- Bảo vệ dữ liệu cá nhân.
- An ninh mạng.
- Giao dịch điện tử.
- Công nghệ thông tin.

Thay vì để LLM trả lời dựa trên kiến thức đã học, hệ thống sử dụng cơ chế Retrieval để tìm kiếm các điều luật liên quan và cung cấp chúng làm ngữ cảnh cho mô hình sinh câu trả lời.

Dự án được phát triển theo hướng **một hệ thống RAG có khả năng triển khai thực tế**, tập trung vào:
- Tối ưu Retrieval.
- Benchmark và đánh giá chất lượng.
- Tracing và Logging.
- Xây dựng API Backend.
- Đóng gói và triển khai bằng Docker.

---

# 2. Kiến trúc tổng quan

```
                         User Question
                                |
                                v
                       Text Normalization
                                |
                                v
                        Hybrid Retrieval
                                |
              +-----------------+----------------+
              |                                  |
              v                                  v
          FAISS + MMR                          BM25
              |                                  |
              +-----------------+----------------+
                                |
                                v
                    Weighted Reciprocal Rank Fusion
                                |
                                v
                            Reranker
                    (BAAI/bge-reranker-v2-m3)
                                |
                                v
                        Prompt Engineering
                                |
                                v
                              LLM
                                |
                                v
                          Final Answer
```

---

# 3. Retrieval Pipeline

## 3.1 Semantic Retrieval - FAISS + MMR

FAISS được sử dụng để tìm kiếm các đoạn văn bản có ý nghĩa ngữ nghĩa gần với câu hỏi.

Kỹ thuật MMR (Maximal Marginal Relevance) được áp dụng để cân bằng giữa:

- Độ liên quan giữa Query và Chunk.
- Độ đa dạng giữa các Chunk được truy xuất.

Điều này giúp hạn chế việc nhiều Chunk có nội dung tương tự xuất hiện trong Top-K.

---

## 3.2 Keyword Retrieval - BM25

Đối với lĩnh vực pháp luật, nhiều thông tin quan trọng phụ thuộc vào từ khóa chính xác như:

- Tên văn bản pháp luật.
- Điều luật.
- Thuật ngữ pháp lý.

BM25 được sử dụng để bổ sung khả năng tìm kiếm theo từ khóa, khắc phục điểm yếu của Semantic Search.

---

## 3.3 Hybrid Retrieval

Kết quả từ FAISS và BM25 được kết hợp bằng chiến lược **Weighted Reciprocal Rank Fusion**:

```
Final Score =
    FAISS_WEIGHT × (1 / Rank_FAISS)
  + BM25_WEIGHT × (1 / Rank_BM25)
```

Cấu hình hiện tại:

- FAISS Weight: 0.7
- BM25 Weight: 0.3

Cấu hình này được lựa chọn dựa trên quá trình benchmark trên tập dữ liệu pháp luật.

---

# 4. Reranking

Sau khi Hybrid Retrieval trả về các ứng viên tiềm năng, hệ thống sử dụng:

**BAAI/bge-reranker-v2-m3**

với kiến trúc Cross-Encoder để đánh giá lại mức độ liên quan giữa Query và từng Chunk.

Ưu điểm:

- Hiểu được mối quan hệ trực tiếp giữa Query và Document.
- Cải thiện thứ tự sắp xếp các Chunk.
- Đưa những ngữ cảnh phù hợp nhất vào LLM.

---

# 5. Đánh giá và Benchmark

Trong quá trình phát triển, hệ thống không lựa chọn các thành phần dựa trên benchmark công khai mà thực hiện đánh giá trực tiếp trên tập dữ liệu pháp luật.

Các thí nghiệm bao gồm:

| Thành phần      |           Nội dung đánh giá               |                       File                        |
|-----------------|-------------------------------------------|---------------------------------------------------|
| Chunking        | So sánh cấu hình Chunk Size và Overlap    | `evaluation/eval_result/chunking_benchmark_v1.md` |
| Embedding       | So sánh Embedding Model khác nhau         | `evaluation/eval_result/embedding_benchmark_v1.md`|
| Hybrid Retrieval| Đánh giá FAISS, BM25 và Hybrid Search     | `evaluation/eval_result/hybrid_benchmark.md`      |
| Reranker        | Đánh giá mức cải thiện sau bước Reranking | `evaluation/eval_result/reranker_benchmark.md`    |
| Generation      | Đánh giá Faithfulness, Semantic Similarity| `evaluation/eval_result/benchmark_generation.md`  |

Các benchmark này giúp đưa ra các quyết định thiết kế như:

- Lựa chọn chiến lược Chunking phù hợp với cấu trúc văn bản pháp luật.
- Chọn Embedding Model dựa trên dữ liệu thực tế.
- Xác định trọng số tối ưu cho Hybrid Retrieval.
- Cân bằng giữa độ chính xác của Reranker và độ trễ của hệ thống.

---

# 6. Backend Architecture

Hệ thống được triển khai dưới dạng FastAPI API với các thành phần hỗ trợ khả năng quan sát (Observability).

```
HTTP Request
      |
      v
RequestContextMiddleware
      |
      + Generate Request ID
      + Extract Query
      + Store Context (ContextVar)
      + Attach RAG Tracer
      |
      v
RAG Pipeline
      |
      + Retrieval
      + Hybrid Search
      + Reranking
      + LLM Call
      |
      v
Response
      |
      v
JSONL Logging + Context Cleanup
```

---

# 7. Logging & Tracing

Để hỗ trợ Debug và theo dõi hệ thống, mỗi Request được gán một `request_id` riêng thông qua `ContextVar`.

Hệ thống ghi lại toàn bộ vòng đời của một Request:

- HTTP Request.
- Retrieval.
- Hybrid Search.
- Rerank.
- LLM Call.
- Final Answer.
- Latency của từng thành phần.

Log được lưu dưới định dạng JSONL giúp dễ dàng phân tích và mở rộng sang các hệ thống giám sát khác.

---

# 8. Công nghệ sử dụng

|      Thành phần      |            Công nghệ             |
|----------------------|----------------------------------|
| Backend API          |            FastAPI               |
| Vector Database      |            FAISS                 |
| Embedding            | HuggingFace Sentence Transformer |
| Semantic Retrieval   |           FAISS + MMR            |
| Hybrid Search        | Weighted Reciprocal Rank Fusion  |
| Keyword Retrieval    |             BM25                 |
| Reranker             |      BAAI/bge-reranker-v2-m3     |
| Orchestration        |            LangChain             |
| Logging              |       JSONL + ContextVar         |
| Deployment           |             Docker               |
| Programming Language |             Python               |
---

# 9. Những thách thức kỹ thuật đã giải quyết

Trong quá trình xây dựng dự án, nhiều vấn đề thực tế đã được nghiên cứu và giải quyết:

- Thiết kế chiến lược Chunking phù hợp với dữ liệu pháp luật.
- Đánh giá và lựa chọn Embedding Model dựa trên dữ liệu Domain.
- Tối ưu Hybrid Retrieval giữa Semantic Search và Keyword Search.
- Phân tích trade-off giữa độ chính xác và độ trễ khi sử dụng Reranker.
- Xây dựng hệ thống Tracing sử dụng Middleware và ContextVar.
- Giải quyết các vấn đề về Dependency, Docker Environment và AI Model Deployment.

Chi tiết quá trình phân tích và các khó khăn được lưu tại:

```
challenges.md
```

---

# 10. Triển khai dự án

Hệ thống hỗ trợ triển khai thông qua Docker.

```
docker build -t legal-rag .
docker run --env-file .env legal-rag
```

---

# 11. Hướng phát triển trong tương lai

- Xây dựng Dashboard theo dõi chất lượng RAG.
- Tích hợp RAG Evaluation tự động.
- Hỗ trợ hội thoại đa lượt với Memory.
- Tối ưu hiệu năng và khả năng mở rộng trên Cloud.



