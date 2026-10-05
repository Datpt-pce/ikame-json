# Cách làm việc trong SLP: chốt trước, code sau

Tài liệu này bổ sung cho `WORKSPACE_PROTOCOL.md` của Codex Room. Protocol quy
định **ai có quyền gì**; tài liệu này quy định **thứ tự làm việc** để một slice
không rơi vào chuỗi reject. Nó không đổi quyền của vai trò nào.

Căn cứ: hồi cứu một slice bảo mật chạy SLP ngày 2026-10-01 có 13 vòng không đạt
(6 vòng RED, 4 source candidate bị reject, 3 vòng source kết thúc không có
candidate) trước khi một candidate được accept. Thiết kế đổi năm lần, lần nào
cũng sau một vòng thất bại; mô hình đe doạ do agent tự đặt và Human không được
hỏi. Sau khi thiết kế được thử trên máy đích, cả 5 RED kế tiếp đều đạt ngay.

## Tiếp nhận yêu cầu (trước mọi việc)

Supervisor hỏi đáp với người dùng trước khi giao Lead:

- Đánh giá độ khó (dễ, trung bình, khó), độ đầy đủ theo 6 mục (mục tiêu,
  đầu vào/đầu ra, phạm vi, môi trường, tiêu chí xong, ràng buộc), và cơ hội
  cùng rủi ro.
- Hỏi bằng thẻ trắc nghiệm, luôn có một phương án khuyến nghị đứng đầu và được
  đánh dấu. Tối đa 3 vòng, mỗi vòng tối đa 3 câu.
- Câu hỏi về rủi ro, chi phí hoặc phạm vi bắt buộc chờ trả lời. Câu hỏi kỹ
  thuật có thể dùng mặc định, và Supervisor ghi rõ giả định.
- Kết thúc bằng gói tiếp nhận không quá một trang gửi Lead: mục tiêu, độ khó,
  tầng sơ bộ, giả định, câu hỏi còn mở kèm mặc định, cơ hội, rủi ro, time-box.

## Bước 0: Phân loại tầng

Ai nhận việc (S hoặc Lead) ghi tầng và ước lượng thời gian trước khi dispatch.
Không có ước lượng thì mặc định T1. Luôn chọn tầng thấp nhất có thể, và chỉ
nâng khi gặp dấu hiệu.

- **T0.** Điều kiện: tool cá nhân, chỉ đọc thông tin local, không quyền admin,
  không chạy nền. Người tham gia: Lead và Writer, không Peer. Time-box: 20 phút.
  Cổng kiểm: Lead soát diff và chạy thử thật.
- **T1.** Điều kiện: việc thường, tiêu chí rõ, có ghi file hoặc config. Người
  tham gia: Lead và Writer, tối đa 1 Peer audit khi Lead không chắc. Time-box:
  40 phút. Cổng kiểm: T2 một lần cho mỗi hash, Lead soát.
- **T2.** Điều kiện: bảo mật, secrets, quyền truy cập, lifecycle tiến trình hoặc
  file. Người tham gia: đủ bước 1–8, 2 Peer review-only. Time-box: theo ngân
  sách Human duyệt ở bước 1. Cổng kiểm: theo bước 6–8.

Dấu hiệu nâng lên ít nhất T1: quét máy khác, cần quyền admin, chạy như service
hoặc nền, đọc process/file của user khác, ghi ngoài thư mục output, đưa vào CI
hoặc máy người khác dùng.

Vượt time-box: Lead dừng, không tự chạy tiếp, và hỏi người dùng để đặt block
thời gian mới phù hợp. Thời gian chờ người dùng trả lời không tính vào
time-box.

## Khi nào áp dụng

| Loại slice | Áp dụng |
| --- | --- |
| Chạm bảo mật, bí mật, quyền truy cập, dữ liệu người dùng, vòng đời tiến trình hay file, hoặc lớp nào trong danh mục lớp lỗi | Toàn bộ các bước 1–8 |
| Thay đổi thường, tiêu chí đã rõ | Bước 4 (ma trận do Lead tự soạn, không cần audit), 6, 7, 8 |
| Sửa nhỏ đã chốt | Lead làm trực tiếp theo protocol; chỉ cần bước 8 |

## Trình tự

```text
1 Human duyệt mô hình đe doạ + ngân sách
2 Lead cân >= 2 phương án, thử primitive trên máy đích, spike nếu kỹ thuật lạ
3 Preflight năng lực runtime
4 Ma trận chấp nhận (nháp) -> 2 Peer review-only, không ghi source -> Lead đóng băng vN
5 RED theo ma trận -> kiểm tính hợp lệ của RED
6 Source -> T1 (writer) -> T2 (Lead, một lần mỗi hash) -> Lead soát từng dòng
7 T3: audit độc lập, báo độ phủ theo lớp -> ACCEPT hoặc REJECT theo lớp
8 Đồng bộ trạng thái tại mốc; đóng phiên Peer
```

### 1. Cổng mô hình đe doạ và ngân sách (Human quyết)

Lead trình Human **một trang, viết bằng lời thường**, trước khi thiết kế:

| Mục | Nội dung |
| --- | --- |
| Tài sản | Cái gì cần bảo vệ, mất nó thì hậu quả gì |
| Trong phạm vi | Ai, làm được gì với máy hay dữ liệu, mà ta sẽ chống |
| Ngoài phạm vi | Ai ta **không** chống, và vì sao chấp nhận được |
| Giới hạn còn lại | Điều vẫn có thể xảy ra sau khi làm xong |
| Ngân sách | Số vòng không đạt tối đa, thời gian, khối lượng ước tính |
| Khuyến nghị | Phương án Lead đề xuất và hệ quả nếu chọn khác |

Audit về sau chỉ được nâng yêu cầu **trong** mô hình đã duyệt. Một phát hiện đòi
chống kẻ tấn công ngoài phạm vi là một đề nghị gửi Human, chưa phải lý do reject.

### 2. Rà phương án và thử trên máy đích

- Ghi ít nhất hai phương án kèm ước lượng chi phí. Một trong số đó phải **loại
  bỏ cả lớp lỗi** thay vì chống lại nó (đổi nơi lưu, dùng cơ chế có sẵn của hệ
  điều hành, bỏ hẳn tính năng).
- Mọi primitive mà thiết kế bắt buộc (hàm hệ thống, chế độ chia sẻ file, API
  runtime) phải có một phép thử chạy được trên chính máy đích trước khi thành
  tiêu chí. Lưu output phép thử.
- Kỹ thuật lạ: giao một Peer làm spike có giới hạn thời gian, trả lời "làm được
  trong một candidate hay phải chia?".
- **Cầu dao chi phí.** Lead dừng và hỏi Human khi thiết kế: thêm một công nghệ
  mới, hoặc làm khối lượng ước tính tăng gấp đôi, hoặc là lần đổi thiết kế thứ
  hai trong cùng slice.

### 3. Preflight năng lực

Một script cố định trong repo dự án in ra: phiên bản runtime thấp nhất phải hỗ
trợ, các API dự định dùng có tồn tại không, hành vi quyền và liên kết của hệ
file, đường dẫn mặc định thực tế. Chạy lại phải cho cùng output. RED không được
viết khi chưa có output này.

### 4. Ma trận chấp nhận

Một bảng duy nhất. Mỗi dòng là một tiêu chí kiểm được.

| ID | Lớp | Tiêu chí (quan sát được) | Cách chứng minh | Tầng | Môi trường | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- |
| AM-RACE-01 | Race | ... | test / lệnh / bước kiểm tay | T1, T2 hoặc T3 | runtime, hệ file | chưa có test / RED / GREEN / không áp dụng + lý do |

Tiêu chí viết trong văn bản thiết kế mà không có cột "cách chứng minh" thì coi
như chưa tồn tại.

Danh mục lớp lỗi. Mỗi lớp phải có ít nhất một dòng, hoặc ghi "không áp dụng"
kèm lý do. Lớp mới phát hiện qua một lần reject được bổ sung vào đây.

| Lớp | Câu hỏi phải trả lời |
| --- | --- |
| Race / TOCTOU | Giữa lúc kiểm và lúc dùng, cái gì có thể đổi, ai đổi được? |
| Atomic publish | Người đọc có bao giờ thấy trạng thái dở dang không? |
| Cleanup | Sau mỗi đường lỗi còn lại file tạm, khoá, tiến trình nào? |
| Handle / tài nguyên | Nhả lúc nào; có phụ thuộc GC hay finalizer không? |
| Mã trả về và đường lỗi | Mọi mã trả về của thao tác hệ thống có được kiểm không? |
| Trạng thái tĩnh và toàn tiến trình | Kiểu, biến tĩnh, module đã nạp có mang trạng thái cũ qua lần nạp lại không? |
| Isolation khi nạp lại | Lần chạy hai có thấy trạng thái của lần một không? |
| Quyền và ACL | Ai được đọc, ghi; lệch thì đóng hay mở? |
| Liên kết và chuyển hướng đường dẫn | Symlink, junction, reparse thì hành vi ra sao? |
| Tương thích runtime | API có tồn tại trên runtime đích thấp nhất không? |
| Năng lực máy đích | Primitive bắt buộc đã chạy được trên máy đích chưa? |
| Đường dẫn và mặc định | Mặc định lấy từ đâu; có giả định máy của người viết không? |
| Hợp đồng giao diện | Test và review có dùng đúng bảng hợp đồng đã chấp nhận không? |
| Seam kiểm thử | Seam có tồn tại trong bản production không; sự kiện của nó có nguyên nhân thật không? |
| Tính xác định của test | Có phụ thuộc thời gian, thứ tự, GC, mạng không? |
| Đồng thời khi kiểm thử | Có dùng chung thư mục build, cổng, khoá với lần chạy khác không? |

Hai Peer làm nhiệm vụ review-only, không ghi source, để audit ma trận trước khi
có source, với hai lăng kính khác nhau (ví dụ: bảo mật và đồng thời; lifecycle
và tương thích). Đây là hợp đồng nhiệm vụ, không phải Paseo mode `read-only`:
provider đã kiểm không đăng ký mode đó. Câu hỏi giao cho họ: "Với từng lớp,
tiêu chí nào còn thiếu, tiêu chí nào không kiểm được?". Lead ra quyết định cho
từng phát hiện rồi đóng băng ma trận thành phiên bản `vN`. Brief của mọi Peer
ghi phiên bản đó.

Sau khi đóng băng, tiêu chí mới chỉ vào qua `REOPEN_REQUEST`, được phân loại
**lớp bị sót** (bổ sung danh mục) hoặc **thông tin mới từ cài đặt**, và làm tăng
phiên bản. Mục tiêu là ít lần mở lại, không phải bằng 0.

### 5. RED hợp lệ

RED chỉ được chấp nhận khi: chạy trên runtime đích; thất bại đúng vì lý do dự
định; cho cùng kết quả qua ba lần chạy liên tiếp; mỗi test trỏ về một ID dòng ma
trận; mọi seam kiểm thử đã có dòng ma trận riêng trước khi được viết.

### 6. Ba tầng kiểm

| Tầng | Ai chạy | Khi nào | Nội dung |
| --- | --- | --- | --- |
| T1 | Writer | Sau mỗi sửa nhỏ | Focused test của phạm vi đang sửa |
| T2 | Lead | **Một lần cho mỗi hash candidate** | Bộ kiểm đầy đủ của dự án (API, typecheck, runtime đích) |
| T3 | Peer audit độc lập | Chỉ sau khi Lead đã soát đủ từng dòng ma trận | Audit theo lăng kính được giao |

Kết quả T2 ghi kèm hash candidate và môi trường; hash không đổi thì không chạy
lại. Tại một thời điểm chỉ một phiên chạy bộ test nặng trên một checkout. Peer
ghi làm trong git worktree riêng:

```bash
git worktree add ../<repo>-wt/<task-id> -b peer/<task-id>
```

Lead tạo Peer với thư mục làm việc là worktree đó, và gỡ worktree sau khi gộp
hoặc sau khi reject không sửa tiếp. Tối đa ba Peer ghi song song cho mỗi Lead.

### 7. Audit, reject và cầu dao

- Brief audit yêu cầu rà **mọi** lớp trong danh mục và trả về cho từng lớp:
  đã rà, không lỗi / đã rà, có lỗi / chưa rà. Audit không dừng ở phát hiện đầu
  tiên. Lead không accept khi còn lớp "chưa rà".
- Phiên audit nhận brief review-only và không ghi source; không chọn một Paseo
  mode `read-only` không tồn tại. Ghi đúng loại: **audit lại** (dùng lại phiên
  cũ để xem phần sửa) hay **audit mới** (phiên mới, dùng cho lần chấp nhận cuối).
- Khi reject, Lead ghi **lớp lỗi**. Writer quét cả lớp đó trên toàn khu vực và
  báo danh sách điểm đã rà trước khi nộp lại.
- Cùng một khu vực bị reject **hai** lần: dừng cài đặt, mở lại ma trận hoặc
  thiết kế. Lần thứ **ba**: báo Human kèm khuyến nghị và hệ quả.

### 8. Trạng thái, ngữ cảnh và vòng đời phiên

- Một nguồn trạng thái chính cho mỗi slice (thường là story). Giữa các mốc chỉ
  cập nhật nguồn này. Spec, sơ đồ và các bề mặt khác đồng bộ tại mốc ACCEPT hoặc
  REJECT của candidate. File chỉ dẫn gốc của dự án (`CLAUDE.md`, `AGENTS.md`)
  không chứa trạng thái lượt chạy.
- Mỗi nhiệm vụ có một **gói ngữ cảnh** dài không quá một trang: mục tiêu, phiên
  bản ma trận, các dòng còn mở, hash candidate, phạm vi ghi, lệnh T1. Peer mới
  phải bắt đầu được từ gói này.
- Dùng Peer mới khi sang giai đoạn lớn, sau hai vòng reject, hoặc sau một lần
  nén ngữ cảnh.
- Lead đóng phiên Peer sau khi ra quyết định ACCEPT/REJECT và Peer đã nhả quyền
  ghi. Peer bị reject cần sửa tiếp thì giữ mở, ghi rõ điểm quay lại.
- Heartbeat: một bản cho mỗi workspace, tên cố định `slp-hb-<slug-workspace>`,
  có hạn tự hết không quá 8 giờ. Trước khi tạo, Supervisor gọi `list_schedules`
  và tái dùng bản trùng tên. Sau ba lần liên tiếp không có thay đổi, giãn chu kỳ
  gấp đôi; có sự kiện mới thì trở lại chu kỳ gốc.

### 8.1. Story riêng cho chi tiết SLP, `specs/` chỉ nhận một dòng

Áp dụng cho dự án đã có thư mục `specs/` theo khung WBS + GTD của toolkit
(`templates/specs/MASTER.md` là index, đọc trước khi mở/tạo/sửa spec — quy
tắc có từ trước ở MASTER.MD mục 9, không phải quy tắc mới của SLP). Đơn vị
trạng thái của SLP là **story**, không phải Work Package: một Work Package
trong `specs/` thường gồm nhiều story theo thời gian, mỗi story mới được
checklist một dòng khi ACCEPT.

- **Nơi ghi chi tiết từng vòng** (ma trận, `Stage`, hash candidate, reject
  theo lớp lỗi, evidence): một story riêng ngoài `specs/`, ví dụ
  `docs/stories/<ID>/` của dự án. Độ chi tiết co theo tầng:
  - T0: không cần story riêng; Lead ghi evidence ngắn ngay trong dòng
    checklist của `specs/` khi xong.
  - T1: một file story đơn (`docs/stories/<ID>.md`), có `Status`, `Lane`
    (= tầng), `Acceptance` dạng checklist.
  - T2: một folder story (`overview.md`, `design.md`, `execplan.md`,
    `validation.md`, `evidence/`), theo đúng mẫu đã dùng cho các slice bảo
    mật trong dự án.
- **`Stage` của story** đi một chiều, không nhảy cóc:

  ```text
  intake → spec-ready → matrix-vN-frozen → red → candidate(hash) → t2 → t3 → accepted
                                                      ↓
                                        rejected(lớp lỗi) → candidate hoặc red
                                        on-hold (chờ Human)
  ```

- **`specs/` chỉ nhận một dòng** tại ACCEPT, REJECT cuối cùng, hoặc on-hold
  cần Human — theo đúng định dạng checklist đã có trong
  `work-package.md`/`project.md`: `- [x] <ngày> — <tóm tắt> [<ID>](<link
  story>)`. Không thêm trường `Tier`/`Stage`/`Candidate` vào file `specs/`.

Phân loại sự kiện (áp dụng cho story, không phải cho `specs/`):

| Loại | Ví dụ | Xử lý |
| --- | --- | --- |
| Không ghi | Tin nhắn trao đổi, output test trung gian, log của Peer | Không ghi vào story |
| Gom lại | Nhiều sửa nhỏ trong cùng một candidate | Ghi một lần tại checkpoint kế tiếp |
| Ghi tại checkpoint | Tiếp nhận xong, đóng băng ma trận vN, candidate có hash mới, ACCEPT, REJECT, đổi tầng, Human quyết định | Chỉ ghi khi qua cổng kiểm |

Cổng kiểm trước khi ghi:

- Có bằng chứng: hash, output test, hoặc tin nhắn quyết định cụ thể.
- Lead là owner duy nhất của story và của dòng checklist trong `specs/`. Peer
  không ghi vào story hay `specs/`, chỉ trả bằng chứng cho Lead.
- `Stage` đi đúng thứ tự trong vòng đời ở trên, không nhảy cóc.
- Hash candidate khớp git hiện tại, và phiên bản ma trận đang dùng khớp story.
- Tầng T0 và T1: Lead tự kiểm bằng checklist trên trước khi ghi dòng vào
  `specs/`. Tầng T2: Supervisor duyệt trước khi Lead ghi dòng đó.

Mục nào thất bại thì không ghi dòng mới vào `specs/`; story giữ `Stage:
on-hold` hoặc `rejected` kèm lý do.

### 9. Usage và ngân sách cho dispatch mới (PSW-002)

- Supervisor dùng `slp-budget.py --root-agent <ID> --compact` tại heartbeat để
  đọc tổng token đã biết và số session `UNKNOWN`. Bỏ `--compact` khi cần chi
  tiết từng phiên. Input bao gồm cached input; reasoning thuộc output, không
  cộng các cột con lần nữa. Đây không phải tiền billing. Agent-phút chưa được
  đo trong bản này.
- Lead không tái sử dụng một session qua nhiều story/slice. Mỗi dispatch mới
  mang title dạng
  `SLP|story|slice|phase|candidate|supervisor/lead/peer|dispatch-id` và các
  label cùng nghĩa (`slp.story`, `slp.slice`, `slp.phase`, `slp.candidate`,
  `slp.dispatch-id`, `slp.role`). Title/label lệch nhau là `UNKNOWN`, không
  được tự quy thuộc.
- Với slice có budget contract, Supervisor/Lead cấp một tranche bằng CLI
  `--admit` trước khi tạo agent. Ledger giữ permit một lần, bind agent ID sau
  create, đóng khi archive; vẫn phải kiểm cả evidence, validation reserve và
  số vòng reject. Ở `shadow`, reason code chỉ là khuyến nghị. Không gọi đó là
  chặn thật.
- Hook `agent.create` của plugin riêng có thể tiêu thụ permit khi một scope
  được bật `enforce`; plugin hiện chỉ là source chưa cài/kiểm qua daemon.
  Không áp dụng hard gate cho `send` tới session có sẵn hoặc tự động dừng
  phiên đang chạy. Chỉ bật sau pilot, rollback và Human chấp thuận.
- Session cũ thiếu log, chia sẻ session ID hoặc không có identity hoàn chỉnh
  được báo `UNKNOWN`; tổng token đã biết là cận dưới. Tránh đưa ra kết luận
  story-level cho session Lead đã chạy qua packet cũ.

### 10. Supervisor xử lý bất đồng Lead–Peer và vòng lặp tốn kém

Supervisor không chọn ý kiến của Lead hay Peer làm kết luận kỹ thuật. Lead vẫn
sở hữu acceptance và quyết định thiết kế; Peer nộp bằng chứng theo brief; Human
sở hữu mục tiêu, chi phí đáng kể và rủi ro. Supervisor sở hữu việc **phát hiện,
đặt câu hỏi và theo đến khi vòng giao tiếp đóng thật**.

| Tín hiệu cần kiểm | Hành động của Supervisor |
| --- | --- |
| Peer phản đối một candidate, Lead chưa disposition tại mốc đã hẹn | Đối chiếu brief → phản hồi thực → quyết định; hỏi Lead bằng câu hỏi mở, không tự viết hộ Peer hoặc accept hộ Lead. |
| Một vòng sửa/audit không tạo executable signal hay bằng chứng mới | Hỏi Lead giả định nào cần thử; không mặc định mở audit rộng hoặc chạy lại T2 khi hash không đổi. |
| Hai reject cùng khu vực/lớp lỗi | Yêu cầu Lead dừng nhánh phụ thuộc và mở lại ma trận/thiết kế hoặc chia slice; giữ việc độc lập đang sẵn sàng chạy. |
| Lần reject thứ ba, hoặc cần đổi mục tiêu/chi thêm ngân sách/chấp nhận rủi ro đáng kể | Trình Human bằng chứng, usage đã biết và phần `UNKNOWN`, cùng khuyến nghị `tiếp tục có hạn / thu hẹp / hoãn / dừng`. |

Mỗi can thiệp dùng một gói ngắn: **candidate hash + dòng ma trận/lớp lỗi +
Peer evidence + Lead disposition hiện có + bằng chứng mới so với vòng trước +
usage delta/validation reserve nếu đo được + mốc quyết định tiếp theo**. Số tin
nhắn và tổng token tăng riêng lẻ không chứng minh lãng phí. Nếu hai bên bất đồng
về một sự thật kiểm được, Lead có thể yêu cầu **một** phép thử hoặc Peer review
độc lập với câu hỏi hẹp và ngân sách rõ; không lấy số phiếu làm kết luận.

Supervisor không tự phát thêm dispatch phụ thuộc vào điểm đang bế tắc. Nếu Lead
vẫn tiếp tục mà chưa xử lý bằng chứng, Supervisor nêu sai lệch mới và báo Human
khi không được giải quyết ở checkpoint. Một lời xác nhận đã đọc không đóng
vòng; phải thấy phản hồi được sửa và quyết định Lead được ghi vào status source.
Quy tắc này là prompt/workflow guard, **chưa phải chặn cơ học** `agent.create`
hay `send` trên host.

## Đoạn chép vào `docs/WORKSPACE_PROTOCOL.md` của dự án

Protocol nguồn cho phép quy tắc cục bộ **bổ sung chi tiết**. Chép đoạn dưới
(tiếng Anh, cùng ngôn ngữ với protocol nguồn) và chỉnh con số cho dự án:

```markdown
## Local supplement: acceptance before source

These rules add detail. They do not change role authority.

- Sensitive slices (security, secrets, access control, user data, process or
  file lifecycle) follow `.agent-toolkit/paseo/SLP-WORKFLOW.md` steps 1-8.
- Human approves the threat model and budget before design. An audit finding
  that needs an out-of-scope adversary is a request to Human, not a rejection.
- Lead records at least two options, one of which removes the failure class,
  and proves every mandated host primitive on the target host first.
- Lead stops and asks Human when a design adds a new technology, doubles the
  estimated size, or changes for the second time in one slice.
- Two Peers do review-only work (no source writes) on the acceptance matrix
  before source. This is a task contract, not a Paseo `read-only` mode: the
  verified provider does not expose that mode. Lead freezes it as vN; every
  brief names the version. New criteria arrive only through REOPEN_REQUEST and
  bump the version.
- Writer runs focused tests only. Lead runs the full project check once per
  candidate hash. Independent audits start only after Lead has checked every
  matrix row, and each audit reports coverage for every failure class.
- A rejection names its failure class; the writer sweeps that class across the
  area before resubmitting. Two rejections of one area reopen the design; a
  third goes to Human.
- One status source per slice. Other surfaces sync at ACCEPT or REJECT.
- Writable Peers work in their own git worktree; at most three in parallel.
  Lead closes a Peer session after its disposition.
- One heartbeat per workspace, named `slp-hb-<workspace-slug>`, expiring within
  8 hours; reuse an existing one, back off when nothing changes.
- New SLP dispatches use a stable title and labels for story, slice, phase,
  candidate and dispatch ID. Do not reuse one Lead session across stories.
- The compact heartbeat usage report shows known cumulative tokens and UNKNOWN
  sessions; open full per-session detail on demand. Shadow budget warnings are
  advisory. Do not claim an active hard gate until its scoped plugin pilot passes.
- On a Lead-Peer stall, Supervisor checks the exact brief, Peer evidence, Lead
  disposition and new executable signal. Two same-class rejects reopen design
  through Lead; a third or material cost/scope/risk decision goes to Human.
  Supervisor does not choose technical winners, direct Peer or accept source.
- Before any dispatch, Supervisor runs intake: classify difficulty,
  completeness (goal, input/output, scope, environment, done-criteria,
  constraints), opportunity and risk. Questions use a multiple-choice card
  with one recommended default, capped at 3 rounds of 3 questions. Risk, cost
  or scope questions wait for a reply; technical ones may default with a
  recorded assumption.
- Every dispatch is classified T0, T1, or T2, defaulting to the lowest tier:
  T0 is a personal tool, local read-only, no admin, no background process
  (Lead + Writer only, 20-minute time-box); T1 is an ordinary change with
  clear criteria (Lead + Writer plus at most one audit Peer, 40-minute
  time-box); T2 is security, secrets, access, or lifecycle work (full steps
  1-8, Human-approved budget). Escalate at least to T1 on scanning other
  hosts, admin rights, background/service execution, another user's data,
  writes outside the output path, or shared/CI machines. Exceeding the
  time-box: Lead stops and asks Human for a new time block, instead of
  continuing silently.
- A Peer objection must cite a test, command, or matrix row. An unevidenced
  objection is decided by Lead within one round. T1 caps challenge at two
  rounds per candidate before Lead decides and records the reason; T2 keeps
  the stall handling above.
- When the project has `specs/` under the toolkit's WBS + GTD layout, slice
  detail (matrix, stage, candidate hash, rejects, evidence) lives in a
  separate story outside `specs/` — a single file for T1, a folder for T2.
  `specs/` only receives one checklist line at ACCEPT, final REJECT, or
  on-hold, in the existing Work Package/Project template. T0 skips a separate
  story; Lead records evidence directly in that one line.
```

## Chỉ số nên theo dõi

| Chỉ số | Ý nghĩa |
| --- | --- |
| Vòng không đạt cho mỗi slice (reject và mở lại) | Kết quả chính |
| Số lần đổi thiết kế sau khi bắt đầu RED | Thiết kế có đứng yên trước tiêu chí không |
| Tiêu chí thêm sau khi đóng băng ma trận | Ma trận có đủ không |
| Vòng source kết thúc không có candidate | Tính khả thi có được xác lập trước không |
| Số lần chạy T2 cho mỗi candidate được accept | Có chạy lặp không |
| Phiên Peer `idle` chưa đóng cuối mỗi khối việc | Vòng đời phiên |
| Known cumulative input/cache/output/reasoning và session `UNKNOWN` theo root/role | Quan sát usage, không giả định `UNKNOWN = 0` |
| Tranche còn lại sau validation reserve, reason code của admission | Quyết định tạo candidate/audit mới |

Không đặt mục tiêu cho số Peer hay số tin nhắn; chỉ theo dõi để phát hiện bất
thường.
