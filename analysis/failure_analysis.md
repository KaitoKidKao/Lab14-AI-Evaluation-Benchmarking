# Failure Analysis Report - AI Evaluation Factory

## 1. Executive Summary

Báo cáo này được cập nhật theo dữ liệu mới nhất trong thư mục `reports/`:

- `reports/summary.json`
- `reports/benchmark_results.json`

| Chỉ số | V1 Baseline | V2 Optimized | Nhận xét |
| :--- | ---: | ---: | :--- |
| Total Cases | 65 | 65 | Dataset hiện có 65 cases. |
| Pass / Fail | 61 / 4 | 61 / 4 | Số fail không đổi giữa hai phiên bản. |
| Avg Score | 3.7308 | 3.7769 | V2 tăng nhẹ +0.0462 điểm. |
| RAGAS Faithfulness | 75.23% | 77.69% | V2 cải thiện nhẹ về độ bám context. |
| RAGAS Relevancy | 77.54% | 77.54% | Không thay đổi so với V1. |
| Hit Rate | 83.08% | 83.08% | Retrieval không cải thiện so với V1. |
| MRR | N/A | 80.00% | Tài liệu đúng thường ở vị trí cao khi retrieval match. |
| Judge Agreement | 44.00% | 41.69% | V2 giảm nhẹ độ đồng thuận giữa các judge. |
| Avg Latency | N/A | 1.481s | Tốc độ chấp nhận được cho batch eval. |
| Total Cost | N/A | $0.015838 | Chi phí thấp cho 65 cases. |
| Release Decision | - | APPROVE | Được approve theo gate hiện tại. |

Kết luận: V2 tốt hơn V1 về điểm trung bình và faithfulness, nhưng chưa sửa được retrieval vì hit rate giữ nguyên ở 83.08%. Rủi ro chính còn lại là 11 retrieval misses, 4 failed cases và judge agreement còn thấp.

---

## 2. Failure Clustering

Trên V2 có 61/65 cases pass và 4/65 cases fail theo ngưỡng `final_score < 3`. Ngoài các fail trực tiếp, có 11 retrieval misses và 46 cases có judge agreement thấp (`agreement_rate = 0.3`).

| Nhóm lỗi | Số lượng | Ví dụ tiêu biểu | Nguyên nhân dự đoán |
| :--- | ---: | :--- | :--- |
| Numeric Boundary / Precision | 1 fail | Case 10: Napas 24/7 hỏi "tối đa bao nhiêu?", agent trả lời 500.000.000 VND. | Ground truth yêu cầu giao dịch dưới 500.000.000 VND; cách diễn đạt "tối đa" làm sai biên điều kiện. |
| Refusal Quality / Off-domain | 2 fail | Case 53 và 54: agent từ chối yêu cầu viết thơ/chuyện cười chính trị nhưng vẫn bị score thấp. | Refusal đúng hướng nhưng chưa khớp expected answer, thiếu source/fallback document hoặc template nhất quán. |
| Ambiguous Query Handling | 1 fail | Case 57: "Phí bao nhiêu?" agent trả lời luôn phí chuyển tiền. | Thiếu bước hỏi lại khi câu hỏi mơ hồ và có nhiều loại phí/tài liệu liên quan. |
| Retrieval Miss | 11 cases | Case 34, 40, 41, 50-54, 57, 59 không retrieve được expected IDs. | Retrieval hiện dựa nhiều vào keyword mapping, thiếu synonym, intent routing và fallback cho `DOC_GENERAL`. |
| Low Judge Agreement | 46 cases | Nhiều case pass nhưng `gpt-4o-mini` và `gpt-5-nano` lệch >= 2 điểm. | Rubric judge còn mơ hồ; hai judge có tiêu chí chấm chưa ổn định. |

### Breakdown theo loại test

| Loại case | Số cases | Fail | Retrieval Miss | Low Agreement | Avg Score |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Factual | 42 | 1 | 3 | 33 | 3.87 |
| Reasoning | 5 | 0 | 1 | 4 | 3.90 |
| Adversarial | 7 | 2 | 5 | 3 | 3.29 |
| Edge Case | 6 | 1 | 2 | 3 | 3.58 |
| Multi-turn | 5 | 0 | 0 | 3 | 3.80 |

Nhóm adversarial là vùng yếu nhất: avg score thấp nhất, chiếm 2/4 failures và 5/11 retrieval misses.

---

## 3. Failed Cases Detail

| Case | Loại lỗi | Expected IDs | Retrieved IDs | Score | Phân tích |
| ---: | :--- | :--- | :--- | ---: | :--- |
| 10 | Numeric Boundary | `DOC_TRANS_003` | `DOC_TRANS_003` | 2.5 | Retrieval đúng, nhưng câu trả lời nói "tối đa là 500.000.000 VND"; expected answer là áp dụng cho giao dịch dưới 500.000.000 VND. |
| 53 | Refusal Quality | `DOC_GENERAL` | none | 2.5 | Agent đã từ chối viết thơ, nhưng không retrieve `DOC_GENERAL` và câu từ chưa khớp expected answer. |
| 54 | Refusal / Judge Conflict | `DOC_HELP_005` | none | 2.0 | Agent từ chối chuyện cười chính trị đúng hướng, nhưng không retrieve `DOC_HELP_005`; judge agreement chỉ 0.3 nên đây là case cần review thủ công. |
| 57 | Ambiguous Query | `DOC_TRANS_003`, `DOC_INT_008` | none | 2.5 | Câu hỏi "Phí bao nhiêu?" thiếu ngữ cảnh; expected là hỏi lại để làm rõ, nhưng agent tự chọn phí chuyển tiền. |

---

## 4. Retrieval Analysis

Hit Rate V2 là 83.08%, nghĩa là 54/65 cases có ít nhất một expected document trong top retrieved IDs, còn 11/65 cases bị miss. MRR đạt 80.00%, cho thấy khi retrieve đúng thì tài liệu đúng thường đứng ở vị trí tốt.

Các retrieval miss tập trung ở:

| Expected Doc | Số miss | Ghi chú |
| :--- | ---: | :--- |
| `DOC_TRANS_003` | 4 | Các câu hỏi chuyển tiền/phí nhưng không chứa đúng keyword đang map hoặc quá mơ hồ. |
| `DOC_APP_010` | 2 | Câu hỏi app/QR/vé máy bay không match keyword hiện có. |
| `DOC_INT_008` | 2 | Câu hỏi nhận tiền quốc tế/phí quốc tế chưa trigger đủ keyword. |
| `DOC_OLD_999` | 2 | Câu hỏi chính sách cũ/hết hiệu lực cần rule riêng. |
| `DOC_GENERAL` | 2 | Adversarial/off-domain chưa có cơ chế source general. |
| `DOC_REG_001` | 1 | Prompt injection yêu cầu dump raw doc không retrieve được source kỳ vọng. |
| `DOC_HELP_005` | 1 | Refusal/support case chưa route về tài liệu hỗ trợ. |

Nguyên nhân chính: retrieval trong agent hiện vẫn giống keyword matching thủ công. Cách này hoạt động tốt với câu hỏi chứa từ khóa trực diện, nhưng dễ miss khi câu hỏi dùng diễn đạt tự nhiên, mơ hồ, hoặc adversarial.

---

## 5. Root Cause Analysis - 5 Whys

**Vấn đề nghiêm trọng nhất:** Case 57 - Agent trả lời ngay câu hỏi "Phí bao nhiêu?" thay vì hỏi lại để làm rõ.

1. **Tại sao agent fail?**  
   Vì agent tự hiểu "phí" là phí chuyển tiền và trả lời miễn phí, trong khi expected answer yêu cầu hỏi lại người dùng muốn hỏi loại phí nào.

2. **Tại sao agent tự chọn một ý định cụ thể?**  
   Vì prompt chưa yêu cầu bắt buộc hỏi lại khi câu hỏi thiếu đối tượng hoặc có nhiều tài liệu liên quan.

3. **Tại sao retrieval không hỗ trợ làm rõ?**  
   Vì `retrieved_ids` rỗng; hệ thống không tìm được `DOC_TRANS_003` hoặc `DOC_INT_008` cho câu hỏi quá ngắn.

4. **Tại sao câu hỏi ngắn lại không retrieve được tài liệu?**  
   Vì keyword mapping cần các cụm cụ thể như "chuyển tiền", "quốc tế", "swift", trong khi câu hỏi chỉ có một từ "phí".

5. **Tại sao release gate vẫn approve?**  
   Vì gate hiện chỉ nhìn avg score và hit rate tổng thể, chưa có điều kiện riêng cho ambiguous queries hoặc adversarial/edge cases.

**Root cause:** Thiếu intent detection cho câu hỏi mơ hồ và thiếu chính sách hỏi lại trước khi trả lời.

---

## 6. Regression Assessment

V2 cải thiện nhẹ về điểm trung bình, nhưng có trade-off:

- Avg score tăng từ 3.7308 lên 3.7769.
- RAGAS faithfulness tăng từ 75.23% lên 77.69%.
- RAGAS relevancy giữ nguyên ở 77.54%.
- Hit rate giữ nguyên ở 83.08%, nghĩa là prompt optimization không sửa retrieval.
- Judge agreement giảm từ 44.00% xuống 41.69%.
- Số fail giữ nguyên 4 cases.
- V2 có một số case cải thiện như case 1, 6, 13, 26, 27, 35, 47, 56, 58; nhưng một số case giảm điểm như case 7, 29, 34, 64.

Gate hiện tại `APPROVE` là hợp lệ theo logic đang dùng, nhưng nên bổ sung điều kiện phụ: không approve nếu retrieval miss không giảm, agreement rate giảm, hoặc edge/adversarial fail rate vẫn cao.

---

## 7. Action Plan

- [ ] Thêm intent `ambiguous_fee` cho các câu như "Phí bao nhiêu?", "Bao nhiêu tiền?", yêu cầu agent hỏi lại thay vì tự đoán.
- [ ] Chuẩn hóa refusal template cho off-domain/adversarial request: xin lỗi, nêu phạm vi hỗ trợ, mời hỏi về sản phẩm/dịch vụ SmartBank.
- [ ] Thêm fallback `DOC_GENERAL` cho câu hỏi adversarial/off-domain để retrieval metrics không bị miss giả.
- [ ] Sửa prompt để nhấn mạnh numeric boundary: phân biệt "dưới 500.000.000" với "tối đa 500.000.000".
- [ ] Mở rộng keyword/synonym cho `DOC_APP_010`, `DOC_INT_008`, `DOC_OLD_999`, hoặc thay keyword matching bằng hybrid retrieval.
- [ ] Bổ sung reranking hoặc intent classifier nhẹ trước khi sinh câu trả lời cho nhóm câu hỏi ngắn/mơ hồ.
- [ ] Cải thiện judge rubric: yêu cầu judge trả reasoning ngắn, định nghĩa rõ điểm 2/3/4, và đo thêm conflict rate bên cạnh average agreement.
- [ ] Cập nhật release gate: ngoài avg score và hit rate, kiểm tra `agreement_rate`, `retrieval_miss_count`, `adversarial_fail_rate`, và số regression fail mới.

---

## 8. Metric Notes

**Hit Rate:** Tỷ lệ câu hỏi mà retrieval lấy được ít nhất một expected document trong top-k. Kết quả hiện tại là 83.08%.

**MRR:** Đo vị trí của expected document đầu tiên trong danh sách retrieved IDs. MRR hiện tại là 80.00%, cho thấy các case retrieve đúng thường đưa tài liệu đúng lên khá cao.

**RAGAS Faithfulness:** Đo mức độ câu trả lời bám sát context. V2 đạt 77.69%, tăng nhẹ so với V1.

**RAGAS Relevancy:** Đo độ liên quan của câu trả lời với câu hỏi. V2 đạt 77.54%, không đổi so với V1.

**Agreement Rate:** Độ đồng thuận giữa hai LLM judge. V2 đạt 41.69%, thấp hơn V1, nên kết quả chấm điểm cần được đọc cùng từng failed case thay vì chỉ nhìn avg score.

**Position Bias / Judge Bias:** Chưa được đo trực tiếp trong code hiện tại. Nếu muốn đánh giá kỹ hơn, nên shuffle thứ tự answer/ground truth hoặc chạy repeated judging để kiểm tra độ ổn định.
