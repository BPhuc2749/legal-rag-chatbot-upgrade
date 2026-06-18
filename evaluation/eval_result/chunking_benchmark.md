# Chunking Benchmark V1

Date: 2026-06-09

Dataset:
- 35 questions
- 7 legal documents

Retriever:
- FAISS
- MMR
- BKAI Vietnamese Bi-Encoder

---

## Results

| Config   | Doc@1  | Doc@3  | Doc@5  | Sec@1  | Sec@3  | Sec@5  |
|----------|--------|--------|--------|--------|--------|--------|
| 800/200  | 74.29% | 88.57% | 94.29% | 34.29% | 48.57% | 65.71% |
| 1000/250 | 71.43% | 88.57% | 97.14% | 28.57% | 60.00% | 71.43% |
| 1250/500 | 71.43% | 94.29% | 97.14% | 34.29% | 65.71% | 71.43% |

---

## Selected Config

1250/500

Reason:
- Highest Doc@3
- Highest Sec@3
- Tied for best Sec@5
- Tied for best Doc@5

---

## Notes

Section Recall có thể bị đánh giá thấp vì một số đoạn văn bản chứa nội dung liên quan nhưng lại mất tiêu đề đoạn văn bản gốc trong quá trình chia nhỏ đoạn văn bản.