# Walkthrough - AI Evaluation Factory (Lab 14)

## 1. Dữ liệu & SDG (Synthetic Data Generation)
- **Knowledge Base**: Đã tạo file `data/knowledge_base.txt` chứa thông tin về hệ thống ngân hàng giả lập (SmartBank) để làm nguyên liệu đánh giá.
- **SDG Engine**: Hoàn thiện `data/synthetic_gen.py` để tự động tạo 50 test cases với đa dạng độ khó:
    - **Easy**: Các câu hỏi tra cứu thông tin trực tiếp.
    - **Hard**: Các câu hỏi yêu cầu giải thích chi tiết.
    - **Adversarial**: Các câu hỏi tấn công prompt (Goal Hijacking).
    - **Edge Cases**: Các câu hỏi ngoài phạm vi tài liệu (Out of Context).
- **Output**: File `data/golden_set.jsonl` đã được tạo thành công.

## 2. Evaluation Engine (Expert Level)
- **Retrieval Evaluation**: Triển khai tính toán **Hit Rate** và **MRR** (Mean Reciprocal Rank) chính xác trong `engine/retrieval_eval.py`.
- **Multi-Judge Consensus**: 
    - Sử dụng cơ chế đồng thuận giữa 2 model (mặc định là `gpt-4o-mini` và `gemini-1.5-flash`).
    - Tính toán **Agreement Rate** để đảm bảo tính khách quan của việc chấm điểm.
    - Tự động cảnh báo nếu hai Judge lệch điểm quá lớn (> 1 điểm).
- **Async Runner**: Tối ưu hiệu năng bằng `asyncio.Semaphore`, cho phép chạy song song 50 cases cực nhanh và có thống kê chi phí/token chi tiết.

## 3. Regression Testing & Release Gate
- **Regression Analysis**: Hệ thống tự động so sánh phiên bản cũ (V1) và phiên bản mới (V2).
- **Auto-Gate**: Triển khai logic quyết định tự động:
    - **APPROVE**: Nếu điểm không giảm và Hit Rate >= 80%.
    - **BLOCK**: Nếu các chỉ số chất lượng không đạt ngưỡng.

## 4. Báo cáo & Phân tích
- **Reports**: Tự động xuất file `reports/summary.json` và `reports/benchmark_results.json`.
- **Failure Analysis**: Đã tạo template `analysis/failure_analysis.md` với các ví dụ thực tế về "Failure Clustering" và "5 Whys" analysis.

---

## Kết quả kiểm thử cuối cùng
Tôi đã chạy script `check_lab.py` và hệ thống đã đạt mọi tiêu chí:
- [x] Tìm thấy đầy đủ các file báo cáo.
- [x] Các chỉ số Hit Rate, Average Score, Agreement Rate đã được tính toán.
- [x] Thông tin Regression Recovery đã sẵn sàng.

> [!TIP]
> Bạn có thể chạy lại toàn bộ pipeline bằng lệnh: `python main.py`
> Và kiểm tra định dạng nộp bài bằng lệnh: `python check_lab.py`

---

