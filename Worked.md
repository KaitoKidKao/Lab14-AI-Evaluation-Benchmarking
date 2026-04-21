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

## 3. Regression Testing & Release Gate (Professional Level)
- **Regression Analysis**: Hệ thống tự động so sánh phiên bản cũ (V1) và bản mới (V2) trên 3 trục chính.
- **Auto-Gate Engine**: Triển khai class `ReleaseGate` chuyên nghiệp với logic quyết định đa chiều:
    - **Quality Gate**: Chặn nếu Điểm trung bình giảm hoặc Hit Rate < 80%.
    - **Performance Gate**: Chặn nếu Latency tăng quá 20% so với baseline.
    - **Cost Gate**: Chặn nếu tổng chi phí vượt ngưỡng ngân sách ($0.05).
- **Decision Reporting**: Tự động xuất báo cáo chi tiết (Decision Report) kèm theo lý do cụ thể cho việc Approve hoặc Rollback, giúp nhóm DevOps dễ dàng theo dõi.

## 4. Báo cáo & Phân tích chuyên sâu
- **Reports**: Tự động xuất file `reports/summary.json` và `reports/benchmark_results.json`.
- **Failure Diagnostics**: Xây dựng tool `analysis/visualize_results.py` cho phép soi chi tiết từng case thất bại:
    - Hiển thị bảng so sánh Đúng/Sai trực tiếp trên Terminal.
    - Xuất file báo cáo chẩn đoán `reports/diagnostics.md` để phân tích sâu nguyên nhân lỗi.

## 5. Tối ưu hóa hệ thống (Expert Optimization)
- **Dynamic Retrieval**: Loại bỏ logic keyword cứng, thay bằng cơ chế tự nhận diện Document ID thông qua LLM Prompting, giúp Hit Rate đạt ngưỡng tuyệt đối ngay cả khi mở rộng tài liệu.
- **Conflict Resolution**: Tinh chỉnh System Prompt để xử lý mâu thuẫn chính sách (Cũ vs Mới) và các ràng buộc phức tạp (Multi-hop).

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

