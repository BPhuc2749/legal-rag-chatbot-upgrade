# Báo Cáo Benchmark Generation

## Dự án

Legal RAG Chatbot

---

# Thông Tin Thí Nghiệm

## Dataset

* Số lượng câu hỏi: 84
* Miền dữ liệu: Tài liệu pháp lý và quy định nội bộ
* Mỗi mẫu dữ liệu bao gồm:

  * Question
  * Ground Truth Answer
  * Generated Answer (RAG Output)
  * Answer Type
  * Difficulty

## Phân bố độ khó

| Difficulty | Số lượng |
| ---------- | -------- |
| Easy       | 28       |
| Medium     | 28       |
| Hard       | 28       |

## Phân bố loại câu hỏi

| Answer Type | Số lượng |
| ----------- | -------- |
| Definition  | 21       |
| List        | 21       |
| Scenario    | 21       |
| Reasoning   | 21       |

---

# Pipeline Sinh Câu Trả Lời

Question

→ Hybrid Search

* FAISS (MMR)
* BM25

→ Ensemble Retriever

* Weight = [0.7, 0.3]

→ Top-20 Chunks

→ Cross Encoder Reranker

* BAAI/bge-reranker-v2-m3

→ Top-5 Chunks

→ Gemini

→ Generated Answer

---

# Các Độ Đo Đánh Giá

## 1. Semantic Similarity

Độ đo này đánh giá mức độ tương đồng ngữ nghĩa giữa:

* Ground Truth
* Generated Answer

Cách tính:

* BKAI Vietnamese Bi-Encoder
* Cosine Similarity

Ý nghĩa:

* 0: Hoàn toàn khác nghĩa
* 1: Cùng ý nghĩa

Lưu ý:

Ground Truth trong bộ dữ liệu được tạo thủ công dựa trên nội dung tài liệu và thường ngắn gọn hơn câu trả lời do hệ thống sinh ra. Vì vậy Semantic Similarity không phản ánh hoàn toàn chất lượng câu trả lời mà chỉ mang tính tham khảo.

---

## 2. Faithfulness

Độ đo này đánh giá mức độ câu trả lời được hỗ trợ bởi các ngữ cảnh đã truy xuất.

Quy trình:

1. Thực hiện lại pipeline Retrieval:

   * Hybrid Search
   * Cross Encoder Reranker

2. Lấy Top-5 Chunk sau Reranker.

3. Đưa vào LLM:

   * Context
   * Generated Answer

4. LLM đóng vai trò giám khảo và chấm điểm từ 0 đến 1.

Ý nghĩa:

* 0: Câu trả lời không được hỗ trợ bởi tài liệu
* 1: Toàn bộ câu trả lời được hỗ trợ bởi tài liệu

Đây là độ đo quan trọng nhất đối với hệ thống RAG vì phản ánh khả năng hạn chế hiện tượng hallucination.

---

## 3. Latency

Đo thời gian phản hồi của toàn bộ pipeline sinh câu trả lời.

Đơn vị:

* Giây (s)

---

# Kết Quả Tổng Thể

| Metric              | Giá trị |
| ------------------- | ------- |
| Semantic Similarity | 0.6115  |
| Faithfulness        | 0.8226  |
| Latency Trung Bình  | 1.66 s  |
| Latency Nhỏ Nhất    | 0.98 s  |
| Latency Lớn Nhất    | 3.91 s  |
| Số mẫu              | 84      |
| Số lỗi              | 0       |

---

# Kết Quả Theo Độ Khó

| Difficulty | Semantic | Faithfulness |
| ---------- | -------- | ------------ |
| Easy       | 0.6505   | 0.8000       |
| Medium     | 0.5914   | 0.8679       |
| Hard       | 0.5926   | 0.8000       |

---

## Phân Tích

### Easy

Có Semantic Similarity cao nhất.

Các câu hỏi chủ yếu yêu cầu truy xuất trực tiếp một thông tin hoặc định nghĩa cụ thể trong tài liệu nên hệ thống trả lời khá chính xác.

---

### Medium

Có Faithfulness cao nhất.

Điều này cho thấy các ngữ cảnh được truy xuất đủ tốt để mô hình sinh câu trả lời bám sát tài liệu.

---

### Hard

Semantic Similarity giảm nhẹ so với Easy.

Nguyên nhân là các câu hỏi khó thường yêu cầu tổng hợp thông tin từ nhiều đoạn khác nhau hoặc cần diễn giải lại nội dung của tài liệu.

Tuy nhiên Faithfulness vẫn duy trì ở mức 80%, cho thấy câu trả lời vẫn chủ yếu dựa trên tài liệu thay vì tự suy diễn.

---

# Kết Quả Theo Loại Câu Hỏi

| Answer Type | Semantic | Faithfulness |
| ----------- | -------- | ------------ |
| Definition  | 0.7032   | 0.9762       |
| List        | 0.5699   | 0.8650       |
| Scenario    | 0.6072   | 0.7000       |
| Reasoning   | 0.5629   | 0.7429       |

---

## Phân Tích

### Definition

Là nhóm có kết quả tốt nhất.

* Semantic Similarity cao nhất
* Faithfulness cao nhất

Điều này cho thấy hệ thống rất phù hợp với các câu hỏi:

* Khái niệm là gì?
* Định nghĩa là gì?
* Ai là đối tượng?
* Quy định nào áp dụng?

Đây là nhóm câu hỏi phổ biến trong các hệ thống Legal RAG.

---

### List

Cho kết quả khá tốt.

Hệ thống có khả năng liệt kê các đối tượng, điều kiện hoặc quy trình được nêu trong tài liệu.

Faithfulness đạt 86.5%, cho thấy phần lớn nội dung được lấy trực tiếp từ tài liệu.

---

### Scenario

Là một trong những nhóm khó hơn.

Các câu hỏi tình huống thường yêu cầu diễn giải hành động cần thực hiện dựa trên quy định.

Faithfulness giảm xuống còn 70%, cho thấy mô hình đôi khi bổ sung thêm nội dung không xuất hiện rõ ràng trong Context.

---

### Reasoning

Là nhóm khó nhất.

Các câu hỏi dạng suy luận thường yêu cầu:

* Kết hợp nhiều thông tin
* Giải thích nguyên nhân
* Suy luận hệ quả

Trong khi RAG truyền thống chủ yếu dựa vào việc truy xuất thông tin nên đây là nhóm có kết quả thấp nhất.

---

# Đánh Giá Chung

## Điểm Mạnh

* Hybrid Search và Cross Encoder Reranker giúp cải thiện đáng kể chất lượng truy xuất.
* Faithfulness đạt trên 82%, cho thấy phần lớn câu trả lời được hỗ trợ bởi tài liệu.
* Hoạt động rất tốt với các câu hỏi định nghĩa và truy xuất thông tin.
* Thời gian phản hồi thấp, trung bình chỉ khoảng 1.66 giây.
* Không phát sinh lỗi trong quá trình benchmark.

---

## Hạn Chế

* Hiệu quả chưa cao với các câu hỏi suy luận.
* Một số câu hỏi tình huống vẫn xuất hiện hiện tượng diễn giải vượt quá Context.
* Semantic Similarity chưa quá cao do Ground Truth thường ngắn gọn trong khi câu trả lời của hệ thống có xu hướng đầy đủ và chi tiết hơn.

---

# Cấu Hình Cuối Cùng Được Lựa Chọn

## Chunking

* Chunk Size: 1250
* Chunk Overlap: 500

## Embedding

* BKAI Vietnamese Bi-Encoder

## Retriever

* FAISS (MMR)
* BM25
* Weight = [0.7, 0.3]

## Reranker

* BAAI/bge-reranker-v2-m3

## Generator

* Gemini

---

# Kết Luận

Kết quả benchmark cho thấy hệ thống Legal RAG đạt chất lượng tốt trên bộ dữ liệu đánh giá gồm 84 câu hỏi.

Các chỉ số chính:

* Semantic Similarity: 61.15%
* Faithfulness: 82.26%
* Latency trung bình: 1.66 giây

Hệ thống đặc biệt hiệu quả đối với các câu hỏi định nghĩa, quy định và truy xuất thông tin pháp lý. Việc kết hợp Hybrid Search và Cross Encoder Reranker giúp đảm bảo câu trả lời được sinh ra bám sát tài liệu và hạn chế hiện tượng hallucination.

Đây là cấu hình phù hợp để triển khai như một trợ lý tra cứu tài liệu pháp lý nội bộ và là nền tảng tốt cho các bước nâng cấp tiếp theo như Query Expansion, Context Compression hoặc Agentic RAG.
