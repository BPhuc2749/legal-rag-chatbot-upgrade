# Benchmark Reranker

## Thông tin thí nghiệm

### Dataset

* Số lượng câu hỏi: 35
* Dữ liệu: Bộ tài liệu pháp lý nội bộ
* Mỗi câu hỏi được gán:

  * expected_doc
  * expected_section
  * section_key

### Cấu hình cố định

#### Chunking

* Chunk Size: 1250
* Chunk Overlap: 500

#### Embedding

* Model: BKAI Vietnamese Bi-Encoder

#### Retrieval Candidate

* Top-K Retrieve: 20

#### Reranker

* Model: BAAI/bge-reranker-v2-m3

#### Evaluation Metrics

##### Document Recall

* Recall@1
* Recall@3
* Recall@5

##### Section Recall

* Recall@1
* Recall@3
* Recall@5

---

# Các cấu hình được so sánh

## 1. FAISS + Reranker

Pipeline:

Question
→ FAISS (MMR)
→ Top 20 chunks
→ BGE Reranker
→ Top 5 chunks

---

## 2. Hybrid + Reranker

Pipeline:

Question
→ FAISS (MMR) + BM25
→ Ensemble Retriever
→ Top 20 chunks
→ BGE Reranker
→ Top 5 chunks

---

# Kết quả Benchmark

| Config          | DOC@1  | DOC@3  | DOC@5  | SEC@1  | SEC@3  | SEC@5  | Time (s) |
| --------------- | ------ | ------ | ------ | ------ | ------ | ------ | -------- |
| FAISS + Rerank  | 85.71% | 88.57% | 94.29% | 48.57% | 71.43% | 74.29% | 25.50    |
| Hybrid + Rerank | 85.71% | 88.57% | 94.29% | 48.57% | 71.43% | 74.29% | 25.42    |

---

# Phân tích kết quả

## Nhận xét chung

Kết quả cho thấy việc bổ sung Reranker giúp cải thiện đáng kể khả năng sắp xếp thứ tự các chunk liên quan.

Mặc dù Recall@5 chỉ tăng nhẹ so với hệ thống Retrieval trước đó, nhưng Recall@1 và Recall@3 được cải thiện rõ rệt.

Điều này phù hợp với bản chất của Reranker:

* Không tìm thêm tài liệu mới.
* Chỉ đánh giá lại mức độ liên quan giữa câu hỏi và các chunk đã được Retrieve.
* Đưa các chunk liên quan nhất lên đầu danh sách kết quả.

---

## So sánh với Hybrid Search trước Reranker

### Trước Reranker

| Metric | Giá trị |
| ------ | ------- |
| DOC@1  | 74.29%  |
| SEC@1  | 45.71%  |
| SEC@3  | 60.00%  |
| SEC@5  | 71.43%  |

### Sau Reranker

| Metric | Giá trị |
| ------ | ------- |
| DOC@1  | 85.71%  |
| SEC@1  | 48.57%  |
| SEC@3  | 71.43%  |
| SEC@5  | 74.29%  |

### Mức cải thiện

| Metric | Improvement |
| ------ | ----------- |
| DOC@1  | +11.42%     |
| SEC@1  | +2.86%      |
| SEC@3  | +11.43%     |
| SEC@5  | +2.86%      |

---

## Phân tích FAISS + Rerank và Hybrid + Rerank

Hai cấu hình cho kết quả gần như giống hệt nhau trên bộ dữ liệu đánh giá.

Điều này cho thấy:

* Candidate chunks được trả về bởi FAISS MMR đã đủ tốt.
* Hybrid Search chưa tạo ra lợi thế rõ rệt trên tập 35 câu hỏi hiện tại.
* Cross Encoder đóng vai trò quyết định trong việc chọn chunk cuối cùng.

Tuy nhiên, do bộ dữ liệu đánh giá còn nhỏ, chưa thể kết luận rằng Hybrid Search không có giá trị.

Trong các hệ thống RAG thực tế với dữ liệu lớn hơn, Hybrid Search thường giúp tăng khả năng Recall đối với các câu hỏi chứa từ khóa pháp lý hoặc các cụm từ đặc thù.

---

# Kết luận

## Cấu hình Retrieval cuối cùng được lựa chọn

### Chunking

* Chunk Size: 1250
* Chunk Overlap: 500

### Embedding

* BKAI Vietnamese Bi-Encoder

### Retriever

* Hybrid Search

  * FAISS (MMR)
  * BM25
  * Weight = [0.7, 0.3]

### Reranker

* BAAI/bge-reranker-v2-m3

---

## Lý do lựa chọn

* Cho kết quả Recall cao nhất trong toàn bộ quá trình benchmark.
* Cải thiện đáng kể chất lượng xếp hạng chunk.
* Tăng mạnh Recall@1 và Recall@3.
* Dễ dàng mở rộng cho các tập dữ liệu lớn hơn trong tương lai.
* Phù hợp để triển khai trong hệ thống Legal RAG Chatbot.

