# Benchmark Hybrid Search

## Thông tin thí nghiệm

### Mục tiêu

Đánh giá hiệu quả của Hybrid Search (FAISS + BM25) trên bộ dữ liệu kiểm thử nội bộ gồm 35 câu hỏi pháp lý.

### Cấu hình

**Embedding Model**

* BKAI Vietnamese Bi-Encoder

**Chunking**

* Chunk Size: 1250
* Chunk Overlap: 500

**Retriever**

* FAISS + MMR
* BM25 Retriever
* EnsembleRetriever

**Hybrid Weight**

* FAISS: 0.7
* BM25: 0.3

**Top-K**

* K = 5

---

## Kết quả Benchmark

| Config                | Doc@1  | Doc@3  | Doc@5  | Sec@1  | Sec@3  | Sec@5  |
| --------------------- | ------ | ------ | ------ | ------ | ------ | ------ |
| Hybrid (FAISS + BM25) | 74.29% | 94.29% | 97.14% | 45.71% | 60.00% | 71.43% |

---

## Nhận xét

### Ưu điểm

* Hybrid Search hoạt động ổn định trên toàn bộ tập dữ liệu.
* Document Recall@5 đạt 97.14%, cho thấy gần như luôn truy xuất được đúng tài liệu trong Top-5 kết quả.
* Document Recall@1 đạt 74.29%, cao hơn một số cấu hình retrieval trước đó.
* Việc kết hợp BM25 giúp cải thiện khả năng truy xuất các truy vấn có từ khóa cụ thể như:

  * Điều luật
  * Khoản
  * Tên thực thể xuất hiện trực tiếp trong văn bản

### Hạn chế của benchmark hiện tại

Bộ dữ liệu đánh giá hiện chỉ gồm 35 câu hỏi nên chưa đủ lớn để đưa ra kết luận thống kê mạnh về hiệu quả của Hybrid Search.

Ngoài ra, Section Recall hiện được đánh giá dựa trên:

* expected_section
* section_key

Trong quá trình chunking, các chỉ mục như:

* 1.2
* Điều 5
* Khoản 3

có thể bị cắt khỏi chunk mặc dù nội dung liên quan vẫn được truy xuất chính xác.

Do đó:

* Section Recall có thể đánh giá thấp hiệu quả thực tế của hệ thống.
* Kết quả Section Recall nên được xem là chỉ số tham khảo thay vì kết luận tuyệt đối.

---

## Kết luận

Hybrid Search cho thấy khả năng truy xuất ổn định và có tiềm năng cải thiện chất lượng retrieval đối với các truy vấn chứa từ khóa cụ thể.

Tuy nhiên, với quy mô tập đánh giá hiện tại và hạn chế của phương pháp đánh giá section-level, chưa có đủ cơ sở để khẳng định Hybrid Search vượt trội hoàn toàn so với baseline FAISS.

Hybrid Search sẽ được giữ lại như một hướng triển khai tiềm năng và tiếp tục được đánh giá trong các giai đoạn nâng cấp tiếp theo của hệ thống RAG.
