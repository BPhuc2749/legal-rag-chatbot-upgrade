# Những khó khăn trong quá trình xây dựng, tối ưu và triển khai Legal RAG Chatbot

Quá trình phát triển Legal RAG Chatbot không chỉ bao gồm việc xây dựng một pipeline RAG cơ bản, mà còn trải qua nhiều khó khăn ở các giai đoạn Benchmark, nâng cấp kiến trúc, tối ưu hiệu năng và Deploy lên môi trường Docker thực tế.

---

# 1. Khó khăn trong việc thiết kế Chunking phù hợp cho dữ liệu pháp luật

Dữ liệu pháp luật có cấu trúc đặc biệt gồm chương, mục, điều, khoản. Vì vậy việc lựa chọn kích thước chunk là một bài toán cân bằng giữa:

- Chunk đủ nhỏ để tăng khả năng Retrieval chính xác.
- Chunk đủ lớn để giữ được đầy đủ ngữ cảnh của một điều luật.

Nhiều cấu hình đã được thử nghiệm như:

- Chunk size 800, overlap 200.
- Chunk size 1000, overlap 250.
- Chunk size 1250, overlap 500.

Ngoài ra, việc đánh giá bằng Section Recall cũng gặp khó khăn vì một điều luật có thể bị chia thành nhiều chunk. Trong một số trường hợp, chunk chứa nội dung đúng nhưng không còn chứa nguyên vẹn `section_key`, dẫn đến việc benchmark đánh giá sai.

Bài học rút ra:

- Không có một kích thước chunk tốt nhất cho mọi bài toán.
- Chunking cần được tối ưu dựa trên đặc điểm dữ liệu thực tế.

---

# 2. Khó khăn trong việc lựa chọn Embedding Model

Mỗi Embedding Model tạo ra một không gian vector khác nhau. Vì vậy khi thay đổi model, toàn bộ Vector Store phải được xây dựng lại.

Ví dụ:

- BKAI Embedding.
- BGE-M3 Embedding.

Mỗi model cần một FAISS Vector Store riêng.

Trong quá trình benchmark, một mô hình có điểm benchmark tổng quát cao hơn chưa chắc hoạt động tốt hơn trên dữ liệu pháp luật. Ví dụ BGE-M3 có Document Recall tốt hơn ở một số mức, nhưng BKAI lại có khả năng truy xuất đúng điều luật tốt hơn.

Bài học rút ra:

- Không nên lựa chọn Embedding chỉ dựa vào benchmark công bố.
- Cần đánh giá trực tiếp trên dữ liệu của hệ thống.

---

# 3. Khó khăn trong việc xây dựng Retrieval hiệu quả

Semantic Search bằng FAISS có khả năng hiểu ý nghĩa câu hỏi nhưng đôi khi bỏ sót các từ khóa pháp lý quan trọng như:

- Số điều luật.
- Tên văn bản pháp luật.
- Thuật ngữ pháp lý cụ thể.

Ngược lại, BM25 tìm kiếm tốt theo từ khóa nhưng không hiểu được ngữ nghĩa.

Do đó hệ thống cần kết hợp:

- FAISS + MMR để khai thác Semantic Search.
- BM25 để tận dụng Keyword Matching.

Tuy nhiên việc lựa chọn trọng số Hybrid cũng là một khó khăn, vì các tỷ lệ khác nhau sẽ tạo ra kết quả Retrieval khác nhau.

Ví dụ:

```
Hybrid Score = 0.7 × FAISS + 0.3 × BM25
```

là kết quả sau nhiều lần benchmark thay vì một giá trị cố định.

---

# 4. Khó khăn trong việc tối ưu Reranker

Một Retriever có thể tìm được đúng tài liệu nhưng chưa chắc sắp xếp đúng thứ tự ưu tiên.

Ví dụ:

- Top 1: Nội dung liên quan nhưng chưa chính xác.
- Top 5: Chứa câu trả lời quan trọng nhất.

Điều này làm giảm chất lượng Context cung cấp cho LLM.

Giải pháp là sử dụng Cross Encoder Reranker để đánh giá lại mức độ liên quan giữa Question và từng Chunk.

Tuy nhiên Reranker cũng tạo ra đánh đổi về hiệu năng:

- Chất lượng Retrieval tăng lên.
- Thời gian xử lý dài hơn, đặc biệt khi chạy trên CPU.

---

# 5. Khó khăn trong việc Benchmark Generation

Việc đánh giá câu trả lời của RAG không đơn giản chỉ là so sánh với Ground Truth.

Các khó khăn bao gồm:

## Xây dựng Faithfulness đúng với pipeline thực tế

Ban đầu việc đánh giá Faithfulness chỉ dựa trên Retrieval đơn thuần, dẫn đến kết quả không phản ánh đúng hệ thống.

Pipeline benchmark sau đó được điều chỉnh thành:

Question  
→ Hybrid Retrieval  
→ Reranker  
→ Top Context  
→ Faithfulness Evaluation

## Sự khác biệt giữa Ground Truth và Generated Answer

Generated Answer thường dài hơn và diễn giải tự nhiên hơn Ground Truth.

Do đó:

- Semantic Similarity thấp không đồng nghĩa với câu trả lời sai.
- Faithfulness cao không đồng nghĩa câu trả lời hữu ích hơn.

Các chỉ số cần được phân tích kết hợp.

## Thiết kế LLM-as-a-Judge

Prompt đánh giá cần đảm bảo:

- Chỉ dựa vào Context.
- Không sử dụng kiến thức bên ngoài.
- Đưa ra điểm số ổn định.

Ngoài ra quá trình benchmark còn gặp giới hạn quota của Gemini API, dẫn đến lỗi `429 RESOURCE_EXHAUSTED`, yêu cầu bổ sung cơ chế Retry và Delay.

---

# 6. Khó khăn trong việc xây dựng hệ thống RAG Tracing và Logging

Đây là một trong những phần khó khăn nhất trong quá trình nâng cấp dự án.

Mục tiêu là theo dõi toàn bộ pipeline:

- HTTP Request.
- Retrieval.
- Hybrid Search.
- Reranking.
- LLM Call.
- Token Usage.
- Latency của từng thành phần.

Các khó khăn chính gồm:

## Quản lý Context trong môi trường bất đồng bộ

FastAPI hoạt động theo cơ chế asynchronous nên không thể sử dụng biến global để lưu trạng thái request.

Giải pháp:

- Sử dụng `contextvars`.
- Xây dựng `RequestContextMiddleware`.
- Tạo `request_id` riêng cho từng request.

## Ghi log JSONL với các object phức tạp

Các object như LangChain Document không thể chuyển trực tiếp sang JSON.

Giải pháp:

Xây dựng cơ chế Safe Serializer để:

- Xử lý đệ quy list và dictionary.
- Chuyển các object không hỗ trợ JSON thành string.

## Đồng bộ dữ liệu giữa các thành phần Pipeline

Sau khi chuyển từ Ensemble Retriever sang Hybrid Retrieval tự xây dựng, dữ liệu trao đổi giữa Retrieval, Reranker và Tracer không còn thống nhất.

Điều này gây ra nhiều lỗi như:

- `TypeError: string indices must be integers`.
- `Document object is not subscriptable`.

Giải pháp:

Thiết kế một cấu trúc Candidate chung chứa:

- Document.
- Chunk ID.
- Điểm FAISS.
- Điểm BM25.
- Hybrid Score.
- Rerank Score.

---

# 7. Khó khăn về Dependency và tương thích môi trường

Khi chuyển từ môi trường Local sang Docker, nhiều vấn đề tương thích xuất hiện.

## Xung đột thư viện Python

Các thư viện như:

- LangChain.
- LangChain Community.
- LangChain Core.
- LangChain Google GenAI.
- Pydantic.

có yêu cầu phiên bản khác nhau, gây lỗi trong quá trình build.

Một vấn đề nghiêm trọng là sự không tương thích giữa FAISS Vector Store và phiên bản LangChain trong Docker, dẫn đến lỗi:

```
KeyError: '__fields_set__'
```

Nguyên nhân là Vector Store được tạo bởi một phiên bản thư viện khác với môi trường Runtime.

Bài học:

- Môi trường tạo Vector Store và môi trường Deploy cần đồng nhất phiên bản.

---

# 8. Khó khăn về Docker, tài nguyên và Machine Learning Dependency

Các thư viện AI như:

- Transformers.
- Sentence Transformers.
- PyTorch.

có dung lượng rất lớn.

Ban đầu Docker tự cài đặt PyTorch bản CUDA, làm:

- Image tăng nhiều GB.
- Tốn RAM WSL2.
- Gây lỗi bộ nhớ trong quá trình build.

Ngoài ra Docker Desktop và WSL2 cũng gặp các lỗi như:

- EOF.
- Read-only file system.
- Input/output error.

Giải pháp:

- Sử dụng PyTorch CPU-only.
- Dọn Docker Cache.
- Tối ưu Docker Image bằng base image nhẹ hơn.

---

# 9. Khó khăn trong việc quản lý AI Model khi Deploy

Khi container khởi động, Embedding Model và Reranker Model được tải từ HuggingFace.

Điều này gây lỗi:

```
requests.exceptions.ReadTimeout
```

do quá trình tải model phụ thuộc vào tốc độ mạng.

Các hướng xử lý bao gồm:

- Download model trước vào Docker Image.
- Sử dụng local cache.
- Lazy Loading model khi cần.

Bài học:

Một ứng dụng AI Production không nên phụ thuộc hoàn toàn vào việc tải model từ Internet khi khởi động.

---

# 10. Khó khăn trong việc cân bằng giữa tối ưu Production và giữ nguyên Source Code

Một vấn đề thực tế là hệ thống chạy ổn định trên Local nhưng khi chuyển sang Docker lại xuất hiện nhiều vấn đề về:

- Dependency.
- Model.
- Bộ nhớ.
- Môi trường Runtime.

Khó khăn nằm ở việc quyết định:

- Refactor kiến trúc để phù hợp Production.
- Hay giữ nguyên Source Code để đảm bảo tính ổn định.

Trong quá trình phát triển, nhiều quyết định được đưa ra dựa trên nguyên tắc:

- Giữ nguyên những thành phần đã hoạt động tốt.
- Tối ưu môi trường triển khai trước.
- Chỉ thay đổi kiến trúc khi thật sự cần thiết.

---

# Tổng kết

Quá trình xây dựng Legal RAG Chatbot cho thấy việc phát triển một hệ thống RAG thực tế phức tạp hơn nhiều so với việc kết nối Vector Database với LLM.

Các thách thức xuất hiện ở nhiều tầng:

1. Thiết kế Chunking phù hợp.
2. Lựa chọn Embedding theo Domain.
3. Xây dựng Hybrid Retrieval.
4. Tối ưu Reranker.
5. Benchmark Generation chính xác.
6. Xây dựng hệ thống Tracing và Logging.
7. Quản lý dữ liệu giữa các thành phần Pipeline.
8. Xử lý Dependency và môi trường Docker.
9. Tối ưu tài nguyên khi triển khai AI.
10. Quản lý Model trong môi trường Production.

Thông qua quá trình này, hệ thống đã được nâng cấp từ một RAG Chatbot cơ bản thành một hệ thống RAG hoàn chỉnh với khả năng Retrieval nâng cao, Reranking, Benchmark, Observability và khả năng triển khai thực tế trên Docker.