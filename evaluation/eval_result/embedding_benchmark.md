# Embedding Benchmark V1

## Thông tin đánh giá

**Ngày đánh giá:** 09/06/2026

**Mục tiêu:**
So sánh chất lượng truy xuất giữa hai mô hình embedding trong hệ thống Legal RAG:

* BKAI Vietnamese Bi-Encoder
* BGE-M3

---

## Cấu hình cố định

### Dataset

* 35 câu hỏi đánh giá
* 7 tài liệu pháp lý

### Chunking

* Chunk Size: 1250
* Chunk Overlap: 500

### Retriever

* Vector Database: FAISS
* Search Type: MMR
* Top K: 5
* Fetch K: 20
* Lambda Mult: 0.8

---

## Kết quả Benchmark

| Embedding | Doc@1  | Doc@3  | Doc@5   | Sec@1  | Sec@3  | Sec@5  |
| --------- | ------ | ------ | ------- | ------ | ------ | ------ |
| BKAI      | 71.43% | 94.29% | 97.14%  | 34.29% | 65.71% | 71.43% |
| BGE-M3    | 74.29% | 91.43% | 100.00% | 42.86% | 68.57% | 68.57% |

---

## Phân tích kết quả

### BKAI Vietnamese Bi-Encoder

Ưu điểm:

* Đạt Section Recall@5 cao nhất (71.43%)
* Đạt Section Recall@3 rất tốt (65.71%)
* Hiệu quả ổn định trên tập dữ liệu pháp lý tiếng Việt
* Là mô hình được huấn luyện chuyên biệt cho tiếng Việt

Nhược điểm:

* Doc Recall@5 thấp hơn BGE-M3 một chút
* Khả năng đưa kết quả đúng lên Top-1 chưa tốt bằng BGE-M3

---

### BGE-M3

Ưu điểm:

* Doc Recall@5 đạt 100%
* Doc Recall@1 cao nhất
* Section Recall@1 cao nhất
* Có khả năng xếp hạng các kết quả liên quan lên vị trí đầu tốt hơn

Nhược điểm:

* Section Recall@5 thấp hơn BKAI
* Chênh lệch tuy nhỏ nhưng vẫn bỏ sót thêm một trường hợp ở mức Top-5

---

## Nhận xét

Kết quả cho thấy hai mô hình có chất lượng khá tương đồng.

BGE-M3 thể hiện khả năng truy xuất tài liệu rất tốt, đặc biệt ở các vị trí Top-1 và Top-3. Tuy nhiên, đối với bài toán Legal RAG hiện tại, mục tiêu quan trọng nhất là đảm bảo phần nội dung liên quan (section) xuất hiện trong tập context cuối cùng được gửi cho LLM.

Ở tiêu chí này, BKAI đạt kết quả tốt hơn:

* BKAI: Section Recall@5 = 71.43%
* BGE-M3: Section Recall@5 = 68.57%

Chênh lệch không lớn nhưng BKAI vẫn là mô hình có kết quả tốt nhất trên bộ benchmark hiện tại.

Ngoài ra, BKAI được tối ưu cho tiếng Việt nên phù hợp với tập tài liệu pháp luật và quy định nội bộ của dự án.

---

## Kết luận

Mô hình embedding được lựa chọn cho phiên bản hiện tại của hệ thống:

**BKAI Vietnamese Bi-Encoder**

Lý do lựa chọn:

1. Đạt Section Recall@5 cao nhất.
2. Hoạt động ổn định trên dữ liệu tiếng Việt.
3. Chất lượng tổng thể tương đương BGE-M3.
4. Phù hợp với mục tiêu tối ưu khả năng truy xuất ngữ cảnh cho Legal RAG.

---

## Baseline Sau Khi Hoàn Thành Benchmark

### Chunking

* Chunk Size: 1250
* Chunk Overlap: 500

### Embedding

* BKAI Vietnamese Bi-Encoder

### Retriever

* FAISS + MMR

### Hiệu năng

* Doc Recall@5: 97.14%
* Section Recall@5: 71.43%

---


