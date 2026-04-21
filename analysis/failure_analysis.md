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

### 1. Hit Rate (Tỷ lệ trúng)
*   **Định nghĩa**: Là tỷ lệ các câu hỏi mà hệ thống Retrieval (tìm kiếm) lấy được **ít nhất một** tài liệu đúng trong Top-K kết quả trả về.
*   **Cách tính**: Nếu tài liệu Ground Truth nằm trong danh sách kết quả trả về -> Hit = 1, ngược lại = 0. Hit Rate là trung bình cộng của tất cả các câu hỏi.
*   **Ý nghĩa**: Trả lời câu hỏi: *"Hệ thống có tìm thấy đúng dữ liệu không?"*. Nếu Hit Rate thấp, AI chắc chắn sẽ trả lời sai (Garbage In, Garbage Out).

### 2. MRR (Mean Reciprocal Rank)
*   **Định nghĩa**: Là chỉ số đánh giá **vị trí (thứ hạng)** của tài liệu đúng đầu tiên tìm được.
*   **Cách tính**: `MRR = 1 / R` (trong đó R là vị trí của tài liệu đúng đầu tiên). Nếu tài liệu đúng ở vị trí số 1 -> điểm là 1. Nếu ở vị trí số 2 -> điểm là 0.5. Nếu không thấy -> điểm là 0.
*   **Ý nghĩa**: Trả lời câu hỏi: *"Tài liệu đúng nằm ở vị trí thứ mấy?"*. MRR càng cao chứng tỏ hệ thống tìm kiếm càng chính xác, tài liệu đúng luôn hiện lên đầu tiên.

### 3. Cohen's Kappa
*   **Định nghĩa**: Là một đại lượng thống kê dùng để đo lường **độ đồng thuận (agreement)** giữa hai người chấm điểm (trong trường hợp của bạn là 2 LLM Judge).
*   **Tại sao cần nó?**: Vì nếu 2 Judge cùng chấm 5 điểm chỉ vì... may mắn (ngẫu nhiên) thì kết quả không đáng tin. Cohen's Kappa loại bỏ yếu tố "may mắn" này để tính toán xem liệu 2 Judge có thực sự "hiểu nhau" và chấm điểm dựa trên cùng một tiêu chí hay không.
*   **Thang đo**: < 0 (không đồng thuận), 0.6 - 0.8 (đồng thuận tốt), 1.0 (đồng thuận tuyệt đối).

### 4. Position Bias (Định kiến vị trí)
*   **Định nghĩa**: Là hiện tượng LLM bị ảnh hưởng bởi **vị trí của thông tin** trong Prompt thay vì nội dung thực tế.
*   **Hai dạng phổ biến**:
    *   **Lost-in-the-Middle**: LLM thường nhớ rất tốt thông tin ở đầu và cuối Prompt nhưng lại "quên" mất thông tin ở giữa.
    *   **Order Bias**: Khi yêu cầu Judge so sánh 2 câu trả lời A và B, nhiều LLM thường có xu hướng chọn câu trả lời A chỉ vì nó xuất hiện trước (hoặc ngược lại).
*   **Cách xử lý**: Để khắc phục, người ta thường đảo vị trí câu trả lời (shuffling) và cho Judge chấm lại lần 2 để xem kết quả có thay đổi không.

