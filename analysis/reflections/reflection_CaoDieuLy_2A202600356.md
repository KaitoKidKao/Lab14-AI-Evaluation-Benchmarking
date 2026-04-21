# Báo cáo Cá nhân - Cao Diệu Ly (2A202600356)

## Vai trò trong nhóm

Trong Lab Day 14, em đảm nhiệm vai trò **Delta Analysis / Regression Analyst**. Trọng tâm công việc của em là đọc kết quả benchmark giữa Agent V1 và Agent V2, phân tích sự thay đổi chất lượng qua các chỉ số định lượng, xác định các failure pattern chính và chuyển kết quả đó thành báo cáo có thể dùng cho quyết định release.

Các artefact em trực tiếp cập nhật gồm:

- `data/golden_set.jsonl`: bổ sung/đưa lại golden dataset 65 cases có ground truth retrieval IDs.
- `reports/summary.json`: tổng hợp kết quả benchmark V1/V2, metrics và release decision.
- `reports/benchmark_results.json`: lưu kết quả chi tiết từng case cho V1 và V2.
- `analysis/failure_analysis.md`: phân tích lỗi, retrieval miss, low judge agreement, regression assessment và action plan.

Bằng chứng commit liên quan trên nhánh `ly`:

- `1333a0d - Update failure analysis report`
- `8c17cc8 - Add golden dataset`

---

## 1. Engineering Contribution (15 điểm)

Đóng góp chính của em nằm ở phần **Regression Testing, Metrics Reading và Failure Analysis**. Sau khi benchmark chạy xong, em không chỉ nhìn vào điểm trung bình mà phân tích toàn bộ dữ liệu trong `reports/benchmark_results.json` để xác định V2 thay đổi như thế nào so với V1.

Cụ thể, em đã tổng hợp các chỉ số:

| Metric | V1 | V2 | Nhận xét |
| :--- | ---: | ---: | :--- |
| Avg Score | 3.7308 | 3.7769 | V2 tăng nhẹ +0.0462 điểm. |
| Hit Rate | 83.08% | 83.08% | Retrieval chưa cải thiện. |
| MRR | N/A | 80.00% | Tài liệu đúng thường nằm ở vị trí cao khi retrieve đúng. |
| Judge Agreement | 44.00% | 41.69% | V2 giảm nhẹ độ đồng thuận giữa judge. |
| RAGAS Faithfulness | 75.23% | 77.69% | V2 bám context tốt hơn. |
| RAGAS Relevancy | 77.54% | 77.54% | Không thay đổi đáng kể. |

Từ các metrics đó, em cập nhật `failure_analysis.md` theo hướng không chỉ ghi "pass/fail", mà chỉ rõ vì sao hệ thống vẫn còn rủi ro dù release gate đang `APPROVE`. Ví dụ: V2 có score cao hơn V1, nhưng Hit Rate không tăng, Judge Agreement giảm và nhóm adversarial vẫn là vùng yếu.

Em cũng phân cụm lỗi theo dữ liệu thực tế:

- 4 failed cases trên V2.
- 11 retrieval misses.
- 46 cases có agreement thấp giữa hai LLM judge.
- Nhóm adversarial có avg score thấp nhất và chiếm 2/4 failures.

Phần này đóng góp trực tiếp vào module đánh giá phức tạp vì nó biến output thô từ Async Runner, Retrieval Metrics và Multi-Judge thành quyết định kỹ thuật rõ ràng: release có thể approve, nhưng cần bổ sung gate phụ cho retrieval miss, adversarial fail rate và judge agreement.

---

## 2. Technical Depth (15 điểm)

### MRR

MRR (Mean Reciprocal Rank) đo vị trí của tài liệu đúng đầu tiên trong danh sách retrieved documents. Nếu tài liệu đúng đứng hạng 1 thì MRR = 1.0; nếu đứng hạng 2 thì MRR = 0.5; nếu không tìm thấy thì MRR = 0.

Trong kết quả hiện tại, V2 có MRR = 80.00%. Điều này cho thấy khi retrieval tìm đúng tài liệu, tài liệu đó thường xuất hiện khá cao. Tuy nhiên Hit Rate chỉ là 83.08%, nghĩa là vẫn có 11/65 cases không retrieve được expected document. Vì vậy vấn đề chính không phải luôn là ranking sai, mà là có một số nhóm câu hỏi retrieval không match được từ đầu.

### Cohen's Kappa / Judge Agreement

Cohen's Kappa là chỉ số đo mức độ đồng thuận giữa hai người chấm sau khi loại trừ khả năng đồng thuận do ngẫu nhiên. Trong lab này hệ thống hiện dùng `agreement_rate` đơn giản hơn để biểu diễn độ lệch giữa hai LLM judge.

V2 có agreement rate 41.69%, thấp hơn V1 là 44.00%. Điều này cho thấy dù điểm trung bình tăng, độ tin cậy của việc chấm điểm chưa thật sự ổn định. Khi hai judge chấm lệch mạnh, em không xem avg score là kết luận cuối cùng mà đọc lại từng failed case, đặc biệt là case 54 khi agent từ chối đúng hướng nhưng vẫn bị score thấp.

### Position Bias

Position Bias là hiện tượng judge hoặc LLM bị ảnh hưởng bởi vị trí thông tin trong prompt, ví dụ ưu tiên answer A vì xuất hiện trước hoặc bỏ sót thông tin nằm giữa context dài. Trong hệ thống eval, bias này có thể làm kết quả chấm không ổn định nếu prompt judge luôn đặt answer, ground truth hoặc context theo một thứ tự cố định.

Để giảm rủi ro này, em đề xuất trong `failure_analysis.md` nên chạy repeated judging hoặc shuffle thứ tự answer/ground truth khi cần đánh giá sâu hơn. Việc này giúp phân biệt lỗi thật của agent với bias của evaluator.

### Trade-off giữa chi phí và chất lượng

Benchmark V2 có tổng cost khoảng `$0.015838` cho 65 cases và latency trung bình 1.481s. Chi phí thấp là lợi thế, nhưng nếu chỉ tối ưu cost bằng model rẻ hơn hoặc giảm judge rounds thì agreement có thể giảm và failure khó phát hiện hơn.

Theo em, trade-off hợp lý là:

- Dùng model rẻ và async runner cho benchmark thường xuyên.
- Chỉ dùng judge mạnh hơn hoặc rerun nhiều lần cho các case conflict, adversarial và regression-sensitive.
- Không mở rộng cost cho toàn bộ dataset nếu vấn đề chỉ tập trung ở vài cluster lỗi.

---

## 3. Problem Solving (10 điểm)

Vấn đề lớn nhất trong quá trình phân tích là kết quả benchmark không thể đọc chỉ bằng một chỉ số duy nhất. Có lúc điểm trung bình tăng nhưng Hit Rate không tăng; có case agent trả lời đúng hướng nhưng judge vẫn cho điểm thấp; có case retrieval đúng nhưng câu trả lời sai ở biên điều kiện.

Cách em xử lý:

- Đối chiếu `summary.json` với `benchmark_results.json` để đảm bảo số liệu tổng hợp khớp case-level results.
- Tách riêng các nhóm lỗi: retrieval miss, numeric boundary, refusal quality, ambiguous query và low judge agreement.
- Không kết luận V2 "tốt hơn hoàn toàn" chỉ vì avg score tăng; thay vào đó ghi rõ trade-off trong Regression Assessment.
- Chọn case 57 làm root cause chính vì nó thể hiện lỗi hệ thống rõ: câu hỏi mơ hồ, retrieval rỗng, agent tự đoán intent và release gate chưa bắt được edge case này.
- Đề xuất action plan cụ thể: thêm intent `ambiguous_fee`, fallback `DOC_GENERAL`, chuẩn hóa refusal template, cải thiện keyword/synonym, thêm reranking/intent classifier và mở rộng release gate.

Qua phần việc này, em hiểu rằng Delta Analysis không chỉ là so sánh hai con số V1/V2. Vai trò này cần truy vết từ metric tổng quan xuống từng case cụ thể, rồi chuyển phát hiện đó thành quyết định engineering có thể hành động được.

---

## Tự đánh giá theo rubric cá nhân

| Hạng mục | Tự đánh giá | Lý do |
| :--- | :---: | :--- |
| Engineering Contribution | 14/15 | Có đóng góp rõ vào golden dataset, reports và failure analysis; phân tích trực tiếp các metrics phục vụ release decision. |
| Technical Depth | 14/15 | Giải thích được MRR, judge agreement/Cohen's Kappa, Position Bias và trade-off cost-quality trong bối cảnh kết quả thật. |
| Problem Solving | 9/10 | Xử lý được dữ liệu benchmark nhiều chiều và chỉ ra action plan cụ thể; có thể cải thiện thêm bằng cách tự động hóa script phân tích failure cluster. |
| **Tổng** | **37/40** | Hoàn thành tốt vai trò Delta Analysis, còn dư địa cải thiện ở phần tự động hóa và đo bias nâng cao. |
