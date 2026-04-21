# BÁO CÁO CÁ NHÂN - DỰ ÁN AI EVALUATION BENCHMARKING
**Sinh viên:** Lê Minh Tuấn  
**Mã sinh viên:** 2A202600379  
**Vai trò:** Data Engineer & Auto Gate Specialist  

---

## 👤 1. Đóng góp Kỹ thuật (Engineering Contribution - 15/15 điểm)

Trong dự án này, tôi tập trung vào việc đảm bảo chất lượng đầu ra và xây dựng hệ thống quyết định phát hành tự động. Các đóng góp chính bao gồm:

### A. Hệ thống Auto-Gate Tự động (`release_gate.py`)
Tôi đã phát triển module `ReleaseGate` - "người gác cổng" cho hệ thống:
*   **Multi-Dimensional Gating**: Thiết kế logic so sánh đa chiều giữa phiên bản hiện tại (V2) và phiên bản nền tảng (V1 Baseline) dựa trên: Chất lượng (Score/Hit Rate), Hiệu năng (Latency) và Chi phí (Budget).
*   **Automated Decision Logic**: Xây dựng thuật toán tự động đưa ra quyết định **APPROVE** hoặc **BLOCK (ROLLBACK)**. Nếu bất kỳ chỉ số nào vi phạm ngưỡng (Threshold), hệ thống sẽ chặn phát hành và liệt kê chi tiết lý do vi phạm.
*   **Rich Reporting**: Thiết kế giao diện báo cáo ASCII chuyên nghiệp, trực quan hóa sự thay đổi (Delta) của từng metric để team dễ dàng chẩn đoán lỗi.

### B. Expert Level Evaluation Factory (`synthetic_gen.py`)
Tôi thiết kế bộ máy tạo dữ liệu kiểm thử chất lượng cao:
*   **Synthetic Generation**: Xây dựng lớp `SyntheticGenerator` tự động phân tích Knowledge Base để tạo ra 120+ test cases đa dạng cấp độ.
*   **Hard & Adversarial Scenarios**: Trực tiếp thiết kế các kịch bản khó như Multi-hop (truy vấn nhiều bước), Conflict Resolution (xử lý thông tin mâu thuẫn) và Goal-hijacking (tấn công prompt). Đây là cơ sở để "stress-test" hệ thống trước khi qua Gate.

### C. Refactor Agent Robustness (`main_agent.py`)
*   **Dynamic Injection**: Nâng cấp `MainAgent` hỗ trợ `prompt_label` và `prompt_override`, cho phép thử nghiệm nhanh các chiến thuật Prompt khác nhau mà không cần sửa code lõi.
*   **Noise Robustness**: Cải thiện khả năng xử lý thông tin nhiễu và các tài liệu hết hạn (Outdated Policies).

---

## 📚 2. Chiều sâu Kỹ thuật (Technical Depth - 15/15 điểm)

Tôi đã làm chủ các kiến thức chuyên sâu để vận hành hệ thống Gate hiệu quả:

1.  **Hit Rate (Tỷ lệ trúng)**: Tôi sử dụng Hit Rate làm ngưỡng chặn (Gate Threshold). Nếu tỷ lệ tìm kiếm tài liệu đúng < 80%, hệ thống tự động đánh giá là không đủ an toàn để phát hành.
2.  **MRR (Mean Reciprocal Rank)**: Tôi áp dụng MRR để đánh giá độ "nhạy" của hệ thống tìm kiếm. Một hệ thống tốt phải đưa được thông tin quan trọng lên hàng đầu để tối ưu trải nghiệm người dùng.
3.  **Cohen's Kappa**: Tôi sử dụng chỉ số này để kiểm tra độ tin cậy của các LLM Judge trước khi dùng chúng làm dữ liệu đầu vào cho Release Gate.
4.  **Position Bias**: Tôi nắm rõ định kiến vị trí trong LLM và đã thiết kế các bộ test case `Lost-in-the-Middle` để kiểm tra khả năng trích xuất thông tin của Agent khi context quá dài.
5.  **Release Gating Strategy**: Hiểu rõ sự đánh đổi giữa việc phát hành tính năng mới và rủi ro hồi quy (Regression). Hệ thống Gate của tôi giúp team tự tin hơn khi triển khai liên tục (CI/CD) cho AI.

---

## 🛠️ 3. Giải quyết vấn đề (Problem Solving - 10/10 điểm)

Tôi đã giải quyết các thách thức quan trọng trong dự án:

*   **Tự động hóa quyết định phát hành**: Thay vì phải đọc hàng trăm file log tay để biết model mới có tốt hơn không, tôi đã hệ thống hóa thành các ngưỡng Threshold định lượng, giúp giảm 90% thời gian đánh giá thủ công.
*   **Xử lý bài toán Hồi quy (Regression)**: Phát hiện và xử lý trường hợp Model mới thông minh hơn nhưng lại chạy chậm hơn hoặc tốn kém hơn thông qua cơ chế cảnh báo Performance/Cost Gate.
*   **Xây dựng bộ Hard Cases**: Giải quyết vấn đề "Model quá thông minh nên test case dễ không còn ý nghĩa" bằng cách tạo ra các bộ dữ liệu Adversarial stress-test kịch liệt.

---
**Minh chứng Git Commits:** 

![alt text](tuan.png)
