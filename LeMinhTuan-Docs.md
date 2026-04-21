# Bàn giao dự án Lab 14 - AI Evaluation Factory (Expert Level)

Đây là tài liệu bàn giao lại toàn bộ kiến trúc, các chỉnh sửa, và những vấn đề đang gặp phải tính đến thời điểm hiện tại. Đồng đội có thể dựa vào file này để tiếp tục phát triển và gỡ lỗi (debug).

---

## 1. Tổng quan công việc đã hoàn thành
Hệ thống hiện tại đã được tiến hóa thành một "Cỗ máy đánh giá AI" chuẩn cấp độ chuyên gia (Expert). Chúng ta không chỉ chạy benchmark đơn thuần, mà đã thiết lập các thử thách hóc búa (giả lập nhiễu từ người dùng, đưa tài liệu cũ vào để bẫy Agent) và xây dựng được công cụ soi chiếu lỗi sâu tận gốc rễ từng câu hỏi một.

## 2. Các vấn đề còn tồn đọng (Pending Issues)
- **Vấn đề cốt lõi:** **Hit Rate vẫn đang ở mức thấp (~48%)**.
- **Nguyên nhân:** Dù đã áp dụng *Few-shot prompting* và đưa thêm chỉ thị *kháng nhiễu*, Agent đôi khi vẫn bị "bối rối" trước các câu hỏi sinh ra từ bộ `synthetic_gen.py` (những câu hỏi cố tình chứa số thứ tự, ký hiệu dư thừa). Một vài case Agent chọn cách từ chối trả lời (False Refusal) do dính vào quy tắc bảo mật khắt khe.
- **Bước xử lý tiếp theo (Next Steps):** 
  - Cần tối ưu thêm file `agent/main_agent.py`. 
  - **Gợi ý kỹ thuật:** Mở rộng phần prompt sang **Chain-of-Thought (Suy nghĩ đa bước)**. Yêu cầu LLM phải "nghĩ lớn tiếng" ra trước: *"Câu hỏi này hỏi về gì? -> Bỏ qua nhiễu -> Tìm trong mục XX -> Mã là DOC_YYY"* trước khi đưa ra câu trả lời cuối.
  - Đồng đội hãy thường xuyên chạy `python analysis/visualize_results.py` để mở file `diagnostics.md` xem cụ thể câu nào Agent đang ngốc nghếch trả lời sai để sửa prompt cho đúng.

---

## 3. Danh sách các File được Thêm mới / Chỉnh sửa

### 3.1. Dữ liệu & Môi trường thử thách
- **`data/knowledge_base.txt` [ĐÃ CHỈNH SỬA]**
  - **Mục đích:** Mở rộng từ 5 lên 12 danh mục. Đưa vào nội dung phức tạp như: chính sách hết hiệu lực (DOC_OLD_999) để tạo bẫy, hạn mức Smart OTP, vay vốn, chuyển tiền quốc tế nhằm stress-test RAG.
  
- **`data/hard_dataset_gen.py` [ĐÃ CHỈNH SỬA]**
  - **Mục đích:** Cung cấp bộ câu hỏi Expert: Kiểm tra sự giao thoa ngưỡng bảo mật (VD: chuyển 15tr dùng SMS hay Smart OTP), bẫy logic quy định cũ-mới, tính toán phí tỷ giá.

- **`data/synthetic_gen.py` [ĐÃ CHỈNH SỬA]**
  - **Mục đích:** Sửa luồng import module. Chúng ta **cố ý giữ lại các nhiễu (noise)** (như chứa số "1.", "2." ở đầu các câu hỏi sinh tự động) để xem khả năng "đề kháng nhiễu" của Agent (vì thực tế user hỏi rất lộn xộn).

- **`data/__init__.py` [TẠO MỚI]**
  - **Mục đích:** Biến thư mục `data` thành một Python package hợp lệ, trị dứt điểm cái lỗi Import phiền phức khi gọi file sinh bộ test.

### 3.2. Bộ não Agent
- **`agent/main_agent.py` [ĐÃ CHỈNH SỬA ĐẬM SÂU]**
  - **Mục đích:** Nâng cấp tư duy (Reasoning) và cơ chế tìm kiếm tài liệu (Dynamic Retrieval) thay cho việc if-else cứng nhắc ban đầu.
  - **Các hàm quan trọng (Đồng đội cần chú ý):**
    - `__init__(self, model_name: str = "gpt-4o-mini")`: Được thiết kế lại để nhận `model_name`. Mục đích để từ `main.py`, tay to có thể ném vào nhiều loại model khác nhau (VD: bản V1 chạy `gpt-4o-mini`, V2 chạy `gpt-4o`) xem mèo nào cắn mỉu nào.
    - `query(self, question: str)`: Chứa bộ não "System Prompt". 
      - Đã thêm lệnh **XỬ LÝ MÂU THUẪN** (ưu tiên nội dung mới).
      - Thêm chỉ thị **XỬ LÝ NHIỄU (ROBUSTNESS)** ép model lờ đi các ký tự rác trong câu.
      - **QUAN TRỌNG:** Thêm phần **FEW-SHOT EXAMPLES** để lùa Agent vào luồng ép xuất chính xác cú pháp `SOURCES: DOC_XXX`. Hàm này cũng chứa code Regex bóc tách `DOC_XXX` để gửi cho bộ chấm điểm chấm Hit Rate. Định sửa Prompt cho Agent thông minh hơn thì sửa tập trung ở đây.

### 3.3. Orchestration & Phân tích lỗi
- **`main.py` [ĐÃ CHỈNH SỬA]**
  - **Mục đích:** Khai báo cụ thể model đang dùng (`gpt-4o-mini`) cấp cho V1 và V2. In choảng ra mặt Terminal đang phân chiếu đánh giá model nào.
  
- **`analysis/visualize_results.py` [TẠO MỚI ĐỘC LẬP]**
  - **Mục đích:** Nếu file `engine/llm_judge.py` là người chấm thi, thì file này là "Giám thị trả bảng điểm". Được thiết kế dưới dạng Zero-Dependency (không xài `pandas` hay thư viện gì ngoài, bảo vệ khỏi vụ lỗi xung đột Anaconda). Quét đống file json khó đọc và in ra một cái bảng chà bá trên Terminal xem câu nào xanh, câu nào đỏ.
  - **Hàm đáng quan tâm:**
    - `visualize_failures(results)`: Vẽ bảng ASCII thần thánh trên log terminal in mười lỗi bự nhất. Phân tách rõ ràng: Sai do "Lôi sai tài liệu (MISS)" hay sai do "Kiến thức (Score thấp)".
    - `export_markdown(results, output_path)`: Tự động ghi chép bệnh lý của Agent ra file markdown `reports/diagnostics.md` để đem ra họp phân tích từ từ.

- **`Worked.md` [ĐÃ CHỈNH SỬA]**
  - **Mục đích:** Đã update checklist các công việc xịn như "Expert Optimization" và "Failure Diagnostics" để phô diễn trình độ của team vào hồ sơ.
