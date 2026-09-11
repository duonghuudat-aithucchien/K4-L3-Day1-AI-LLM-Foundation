# K4 — Ngày 1: Bài Tập & Phản Ánh
## Khám Phá LLM API | Phiếu Thực Hành

**Thời lượng:** 4 tiếng
**Cách làm:** Trả lời từng câu ngay sau khi hoàn thành block tương ứng —
đừng để dồn hết về cuối buổi. Thay dòng `*Câu trả lời của bạn*` bằng câu
trả lời thật (chấm tự động sẽ đếm số câu đã trả lời).

---

## Block 1 — API Cơ Bản (trả lời sau Checkpoint 1)

### Câu 1.1 — Độ nhạy của temperature
Gọi `call_openai` với temperature 0.0, 0.5, 1.0 và 1.5 dùng prompt
**"Hãy kể cho tôi một sự thật thú vị về Việt Nam."**

**Bạn nhận thấy quy luật gì qua bốn phản hồi?** (2–3 câu)
> Khi temperature thấp (0.0 - 0.5), phản hồi có tính xác định cao, câu từ ngắn gọn, tập trung vào các sự thật phổ biến nhất (như xuất khẩu cà phê hay hang Sơn Đoòng) và hầu như không đổi khi gọi lại. Khi temperature tăng lên 1.0 và 1.5, văn phong trở nên đa dạng, phong phú hơn nhưng ở mức 1.5 câu chữ bắt đầu lan man, cấu trúc câu kém tự nhiên và dễ xuất hiện hiện tượng bịa đặt (hallucination). Quy luật chung là temperature càng cao thì tính ngẫu nhiên và sáng tạo càng tăng, nhưng đánh đổi lại là sự suy giảm tính ổn định và độ chính xác thực tế.

### Câu 1.2 — Chọn temperature cho sản phẩm
**Bạn sẽ đặt temperature bao nhiêu cho chatbot hỗ trợ khách hàng, và tại sao?**
> Tôi sẽ đặt temperature trong khoảng từ 0.0 đến 0.2 (thường ưu tiên 0.0 hoặc 0.1). Lý do là chatbot chăm sóc khách hàng đòi hỏi độ chính xác tuyệt đối, thông tin về chính sách, giá cả và quy trình phải nhất quán, có thể kiểm chứng được, tránh tối đa việc model trả lời ngẫu hứng hoặc bịa đặt thông tin gây hiểu lầm cho người dùng.

### Câu 1.3 — Đánh đổi chi phí
Kịch bản: 10.000 người dùng hoạt động mỗi ngày, mỗi người gọi API 3 lần,
mỗi lần trung bình ~350 token đầu ra.

**Ước tính GPT-4o đắt hơn GPT-4o-mini bao nhiêu lần cho workload này? Nêu một
trường hợp GPT-4o xứng đáng với chi phí và một trường hợp nên dùng mini:**
> - Ước tính chi phí: Tổng token output/ngày là 10.000 × 3 × 350 = 10.500.000 token (10.500K token). Theo bảng giá, output của GPT-4o là $0.010/1K token ($105/ngày), còn GPT-4o-mini là $0.0006/1K token ($6.3/ngày). Do đó GPT-4o đắt hơn GPT-4o-mini khoảng 16.67 lần (gấp gần 17 lần).
> - Trường hợp GPT-4o xứng đáng chi phí: Các tác vụ phân tích hợp đồng pháp lý, chuẩn đoán y khoa, xử lý logic tài chính đa bước hoặc lập trình hệ thống phức tạp đòi hỏi khả năng suy luận chuyên sâu và ít sai sót.
> - Trường hợp nên dùng GPT-4o-mini: Chatbot trả lời câu hỏi thường gặp (FAQ), phân loại ý định (intent classification), trích xuất thông tin cơ bản hoặc tóm tắt đoạn văn ngắn với lưu lượng người dùng cực lớn hàng ngày.

---

## Block 2 — System Prompt & Token (trả lời sau Checkpoint 2)

### Câu 2.1 — Sức mạnh của persona
Gọi `chat_with_system_prompt` hai lần với cùng câu hỏi
**"Giải thích blockchain là gì?"** nhưng hai system prompt khác nhau:
- "Bạn là giáo viên tiểu học, giải thích thật đơn giản cho trẻ 8 tuổi."
- "Bạn là chuyên gia tài chính, trả lời chuyên sâu bằng thuật ngữ kỹ thuật."

**Hai phản hồi khác nhau như thế nào (độ dài, từ vựng, ví dụ)? System prompt
ảnh hưởng đến hành vi model ra sao?** (3–4 câu)
> Phản hồi của vai giáo viên tiểu học sử dụng từ ngữ gần gũi, câu văn ngắn gọn, lấy hình ảnh ẩn dụ trực quan (như cuốn sổ ghi chép chung của cả lớp mà ai cũng có một bản sao để không ai gian lận được). Ngược lại, vai chuyên gia tài chính sử dụng hệ thống thuật ngữ chuyên môn dày đặc (sổ cái phân tán - distributed ledger, mật mã học phi tập trung, thuật toán đồng thuận Proof of Work/Stake, tính bất biến - immutability) và tập trung phân tích cấu trúc thanh toán, loại bỏ bên trung gian. System prompt đóng vai trò như một bộ lọc định hình toàn diện phong cách phát ngôn, chiều sâu kiến thức và đối tượng mục tiêu mà không cần người dùng phải thay đổi câu hỏi gốc.

### Câu 2.2 — tiktoken vs đếm từ
Chọn một đoạn văn tiếng Việt ~100 từ. So sánh số token theo `count_tokens`
(tiktoken) với ước lượng `số từ / 0.75` mà Part 1 đã dùng.

**Hai con số chênh nhau bao nhiêu phần trăm? Vì sao tiếng Việt thường tốn
nhiều token hơn tiếng Anh cùng độ dài?**
> Với đoạn văn tiếng Việt 100 từ, công thức ước lượng `100 / 0.75 ≈ 133 token`, nhưng khi đo thực tế bằng `count_tokens` (tiktoken) kết quả thường rơi vào khoảng 160 – 185 token, chênh lệch cao hơn khoảng 20% – 38%. Tiếng Việt tốn nhiều token hơn tiếng Anh vì tokenizer (như Byte-Pair Encoding) được huấn luyện chủ yếu trên kho ngữ liệu tiếng Anh nên hầu hết từ tiếng Anh thông dụng chỉ tốn 1 token; trong khi đó, tiếng Việt có thanh dấu và ký tự Unicode đa byte, các từ ghép hoặc từ có dấu thường bị băm thành nhiều mảnh subword hoặc byte token riêng lẻ.

---

## Block 3 — Streaming & Độ Bền (trả lời sau Checkpoint 3)

### Câu 3.1 — Trải nghiệm người dùng với streaming
**Streaming quan trọng nhất trong trường hợp nào, và khi nào thì
non-streaming lại phù hợp hơn?** (1 đoạn văn)
> Streaming quan trọng nhất trong các ứng dụng có tính tương tác trực tiếp với người dùng như chatbot hội thoại, trợ lý ảo hoặc công cụ hỗ trợ viết nội dung dài; việc hiển thị từng từ theo thời gian thực giúp giảm đáng kể thời gian chờ nhận token đầu tiên (Time-To-First-Token - TTFT), mang lại cảm giác phản hồi tức thì và người dùng có thể đọc ngay thay vì nhìn màn hình đứng yên. Ngược lại, non-streaming lại phù hợp hơn trong các tác vụ ngầm (background jobs), xử lý theo lô (batch processing), các lời gọi API backend giữa các server với nhau hoặc khi ứng dụng cần nhận về dữ liệu có cấu trúc đầy đủ (như JSON / Structured Outputs) để parse và validate trước khi xử lý bước tiếp theo.

### Câu 3.2 — Vì sao backoff theo cấp số nhân?
**So với delay cố định (ví dụ luôn chờ 1 giây), exponential backoff có lợi
thế gì khi API bị quá tải? Điều gì xảy ra nếu hàng nghìn client cùng retry
với delay cố định giống nhau?**
> So với delay cố định, exponential backoff có lợi thế là tự động kéo giãn khoảng thời gian giữa các lần thử lại ngày một dài hơn (0.1s → 0.2s → 0.4s...), qua đó tạo ra một "khoảng thở" quý giá giúp hệ thống server đang chịu tải có đủ thời gian giải phóng hàng đợi và khôi phục trạng thái ổn định. Nếu hàng nghìn client cùng retry với một khoảng delay cố định giống nhau, toàn bộ các client sẽ đồng loạt gửi lại request vào cùng một thời điểm sau mỗi chu kỳ, tạo nên hiện tượng sóng truy vấn dồn dập (Thundering Herd Problem); điều này làm server vừa thoát nghẽn lại lập tức rơi vào tình trạng quá tải nghiêm trọng hơn.

---

## Block 4 — Mini-Project (trả lời sau Checkpoint 4)

### Câu 4.1 — Thiết kế persona
**Bạn chọn persona gì cho trợ lý của mình? Viết lại system prompt đó và giải
thích 1–2 lựa chọn từ ngữ quan trọng trong prompt (ví dụ: vì sao yêu cầu
"trả lời ngắn gọn", vì sao chỉ định ngôn ngữ...):**
> - System prompt được chọn: *"Bạn là trợ giảng lập trình AI thân thiện và kiên nhẫn. Luôn trả lời ngắn gọn (dưới 150 từ), giải thích bằng tiếng Việt tự nhiên và cung cấp ví dụ code minh họa tối giản khi giải thích khái niệm."*
> - Giải thích các lựa chọn từ ngữ:
>   1. *"ngắn gọn (dưới 150 từ)"*: Giúp tiết kiệm output token, kiểm soát chi phí API và giúp người học nắm bắt trọng tâm nhanh chóng ngay trên giao diện dòng lệnh (CLI terminal) thay vì bị ngợp bởi các đoạn văn bản dài.
>   2. *"thân thiện và kiên nhẫn, giải thích bằng tiếng Việt tự nhiên"*: Giúp giảm rào cản tâm lý cho người mới bắt đầu học AI/Python, tạo cảm giác được đồng hành và giải quyết vấn đề từng bước dễ hiểu.

### Câu 4.2 — Hạn chế & cải thiện
**Trợ lý của bạn hiện có hạn chế lớn nhất là gì (ví dụ: history chỉ 3 lượt,
không có bộ nhớ dài hạn, không kiểm duyệt nội dung...)? Đề xuất một cải
thiện cụ thể và mô tả ngắn cách triển khai:**
> - Hạn chế lớn nhất: Cơ chế cắt cứng history (fixed-window truncation: giữ tối đa 3 lượt / 6 message gần nhất) khiến trợ lý bị "mất trí nhớ ngắn hạn" khi cuộc trò chuyện kéo dài; người dùng không thể nhắc lại các biến, giả định hay yêu cầu đã thảo luận từ 4 lượt trước.
> - Đề xuất cải thiện: Triển khai cơ chế **Conversation Summary Buffer (Tóm tắt ngữ cảnh tự động)**.
> - Mô tả cách triển khai: Khi lịch sử hội thoại vượt quá ngưỡng (ví dụ > 6 messages), thay vì cắt bỏ hoàn toàn các message cũ nhất, hệ thống sẽ dùng một model nhỏ, rẻ (như `gpt-4o-mini`) chạy một lời gọi API ngầm để tóm tắt các lượt trao đổi cũ thành một đoạn tóm tắt ngắn gọn (`summary`). Sau đó, đoạn tóm tắt này được tiêm vào ngay dưới system prompt làm ngữ cảnh nền (background context). Bằng cách này, bot vẫn duy trì được thông tin quan trọng xuyên suốt toàn bộ phiên trò chuyện mà không làm tăng vọt số lượng token input.

---

## Danh Sách Kiểm Tra Nộp Bài

- [ ] `python grade.py` — xem điểm tự động, mục tiêu ≥ 75/100
- [ ] Cả 4 checkpoint pytest đều pass
- [ ] Tất cả 9 câu trong file này đã được trả lời
- [ ] Đã copy bài làm vào folder `solution/`, push lên fork và dán link trên trang bài Lab ở VLearn trước 23:59 ngày 11/09/2026
