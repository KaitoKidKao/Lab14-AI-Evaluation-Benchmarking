# BÁO CÁO CÁ NHÂN - LAB 14

**Họ và tên:** Đậu Văn Nam  
**MSSV:** 2A202600033  
**Vị trí:** AI & Backend  

---

## 👤 2. Điểm Cá nhân (Tối đa 40 điểm)

| Hạng mục | Tiêu chí | Điểm |
| :--- | :--- | :---: |
| **Engineering Contribution** | - Đóng góp cụ thể vào các module phức tạp (Async, Multi-Judge, Metrics).<br>- Chứng minh qua Git commits và giải trình kỹ thuật. | 15 |
| **Technical Depth** | - Giải thích được các khái niệm: MRR, Cohen's Kappa, Position Bias.<br>- Hiểu về trade-off giữa Chi phí và Chất lượng. | 15 |
| **Problem Solving** | - Cách giải quyết các vấn đề phát sinh trong quá trình code hệ thống phức tạp. | 10 |

---

## 🛠 3. Chi tiết đóng góp kỹ thuật

Trong bài Lab này, tôi chịu trách nhiệm chính về hạ tầng thực thi (`main.py`) và logic cốt lõi của Agent (`main_agent.py`).

### 1. Module `agent/main_agent.py`: Nâng cấp Agent & Retrieval
- **Hỗ trợ Multi-turn:** Cập nhật phương thức `query` để xử lý danh sách `messages` (hội thoại đa lượt), giúp Agent hiểu ngữ cảnh từ các câu hỏi trước đó thay vì chỉ xử lý câu hỏi đơn lẻ.
- **Tối ưu Hit Rate:** Xây dựng bộ Keyword Mapping mở rộng phủ khắp 11 mã tài liệu nghiệp vụ ngân hàng. Qua đó, nâng chỉ số **Hit Rate**, vượt mục tiêu đề ra ban đầu (>80%).
- **Standardizing Sources:** Loại bỏ cơ chế fallback `DOC_GENERAL` gây nhiễu kết quả đánh giá, đảm bảo retrieval chỉ trả về các tài liệu thực sự khớp với truy vấn.

### 2. Module `main.py`: Regression Analytics & Release Gate
- **Regression Pipeline:** Phát triển quy trình chạy song song Phase 1 (Baseline) và Phase 2 (Optimized). Tự động gộp dữ liệu để so sánh trực tiếp hiệu năng giữa 2 phiên bản.
- **Expert Reporting:** Thiết kế cấu trúc file `summary.json` và `benchmark_results.json` theo chuẩn Expert, bao gồm các chỉ số RAGAS (faithfulness, relevancy) và chi tiết lý lẽ (reasoning) từ từng model Judge.
- **Auto Decision Logic:** Cài đặt logic "Release Gate" tự động đưa ra quyết định `APPROVE` hoặc `BLOCK` dựa trên delta score và ngưỡng Hit Rate.

---

## 🧠 4. Thấu hiểu kỹ thuật (Technical Depth)

- **MRR (Mean Reciprocal Rank):** Tôi đã áp dụng MRR để đo lường mức độ hiệu quả của retrieval. Khác với Hit Rate (chỉ cần tìm thấy), MRR ưu tiên việc tài liệu đúng xuất hiện ở vị trí đầu tiên. Kết quả đạt ~76% cho thấy hệ thống đang đưa thông tin chính xác nhất lên rất cao.
- **Trade-off Chi phí & Chất lượng:** Trong quá trình tối ưu, tôi sử dụng `gpt-4o-mini` cho Agent để tiết kiệm chi phí nhưng dùng mô hình Multi-Judge (gpt-4o-mini & gpt-5-nano) với nhiệt độ (temperature) khác nhau để tăng độ tin cậy. Việc này tăng nhẹ Latency (~1.2s) nhưng đảm bảo được tính khách quan trong chấm điểm.
- **Judge Conflict & Bias:** Thông qua `individual_results`, tôi quan sát thấy hiện tượng các model Judge có xu hướng lệch điểm (conflict). Tôi đã giải quyết bằng cách tính `agreement_rate` để cảnh báo những trường hợp điểm số không ổn định.

---

## 🚀 5. Giải quyết vấn đề (Problem Solving)

- **OpenAI JSON Error:** Gặp lỗi 400 khi dùng `response_format: json_object` do Prompt không chứa từ khóa "json". Tôi đã xử lý bằng cách lập trình tự động bổ sung tiền tố định dạng vào cuối mọi prompt gửi đến Judge.
- **Handling Multi-turn Text:** Do bộ dữ liệu ban đầu lưu history dưới dạng chuỗi thô trong trường "question", tôi đã viết logic xử lý linh hoạt để Agent có thể phân tách ngữ cảnh và trả lời đúng ý định người dùng (như các case về "hạn mức cũ" vs "hạn mức mới").

---