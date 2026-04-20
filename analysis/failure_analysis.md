# Failure Analysis Report - AI Evaluation Factory

## 1. Failure Clustering (Phân nhóm lỗi)
Dựa trên kết quả chạy benchmark, các lỗi được phân nhóm như sau:

| Nhóm lỗi | Số lượng | Ví dụ tiêu biểu | Nguyên nhân dự đoán |
| :--- | :---: | :--- | :--- |
| **Hallucination** | 2 | Trả lời sai về hạn mức thẻ tín dụng. | Retrieval tìm sai chunk hoặc LLM bị "bịa" số. |
| **Retrieval Miss** | 5 | Không tìm thấy thông tin về nuôi mèo. | Thông tin không có trong Knowledge Base (đúng kỳ vọng). |
| **Goal Hijacking** | 1 | Agent viết thơ về Bitcoin thay vì từ chối. | System Prompt chưa đủ chặt chẽ để chặn tấn công. |
| **Low Agreement** | 3 | Hai Judge lệch nhau 2 điểm về độ chuyên nghiệp. | Rubrics còn mập mờ, cần định nghĩa rõ hơn. |

---

## 2. Root Cause Analysis (5 Whys)
Phân tích sâu một trường hợp lỗi nghiêm trọng nhất.

**Vấn đề:** Agent trả lời sai quy trình đăng ký tài khoản (Hallucination).

1. **Tại sao Agent trả lời sai?**
   - Trả lời: Vì thông tin trong câu trả lời không khớp với DOC_REG_001.
2. **Tại sao thông tin không khớp?**
   - Trả lời: Vì đoạn văn bản (context) gửi vào LLM chứa thông tin về Thẻ tín dụng Thay vì Đăng ký tài khoản.
3. **Tại sao context lại sai?**
   - Trả lời: Vì công cụ Retrieval (Vector Search) trả về DOC_CARD_004 ở vị trí Top 1.
4. **Tại sao Retrieval lại trả về kết quả sai?**
   - Trả lời: Vì câu hỏi của người dùng có chứa từ khóa "đăng ký" nhưng trong tài liệu Thẻ tín dụng cũng có cụm từ "đăng ký mở thẻ Platinum".
5. **Tại sao hệ thống không phân biệt được sự khác biệt này?**
   - Trả lời: Do chiến lược Chunking quá nhỏ (50 tokens) làm mất ngữ cảnh toàn cư của đoạn văn, dẫn đến Keyword overlap gây nhiễu.

**Giải pháp đề xuất:** Tăng kích thước Chunk lên 500 tokens và thêm Metadata Filtering theo danh mục.

---

## 3. Đề xuất cải tiến (Action Plan)
- [ ] Cải thiện System Prompt để chặn Goal Hijacking.
- [ ] Tinh chỉnh Chunking strategy (Overlap 10-20%).
- [ ] Bổ sung thêm 1 Agent version mới (V3) sử dụng Hybrid Search (Vector + Fulltext).
