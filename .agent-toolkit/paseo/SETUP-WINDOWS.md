# Đề xuất Paseo SLP trên Windows

Khi dự án dùng github-agent-toolkit, hãy **đề xuất** bộ Codex Room SLP ba vai
trò cho người dùng nếu họ muốn nhiều agent hoặc điều phối qua Paseo. Trên
Windows có Paseo, chạy bootstrap toolkit sẽ tự cập nhật host từ **commit ghim
đã duyệt** của repo nguồn sau khi khởi tạo project, rồi áp
[`local-policy.toml`](local-policy.toml). Chỉ đọc folder thì không chạy. Cách
làm việc trong SLP (chốt mô hình đe doạ, ma trận chấp nhận, ba tầng kiểm) nằm
ở [SLP-WORKFLOW.md](SLP-WORKFLOW.md).

Chuẩn đã kiểm chứng ngày 2026-09-29 trên Windows native: ba Paseo Agent Profile
`Codex Room Supervisor`, `Codex Room Lead`, `Codex Room Peer`; ba alias
`codex-supervisor`, `codex-lead`, `codex-peer`. Supervisor dùng
`gpt-5.6-sol/medium`; Lead chọn `gpt-5.6-sol/high|xhigh` hoặc
`gpt-6-sol/medium`; Peer chọn `gpt-5.6-terra/high|xhigh|max`. Lead và Peer
mặc định ở mức `high`; profile giữ mặc định, provider cung cấp lựa chọn khác
khi tạo phiên.
Supervisor/Lead có Paseo tools, Peer không. Ba vai trò dùng ba `CODEX_HOME`
riêng; skills và plugins chia sẻ qua junction, còn `auth.json` là bản sao được
đồng bộ theo thời gian ghi.

## Tự cập nhật khi chạy bootstrap

Từ project, chạy `python <đường-dẫn-toolkit>/bootstrap.py --target <project>`.
Khi Paseo đã được cài, bootstrap tải năm file dữ liệu từ commit ghim (hoặc
commit `main` mới nhất nếu gọi rõ `--paseo-source latest`), kiểm cấu trúc role và model/effort trong catalog Codex, backup host,
cập nhật ba runtime/profile, và reload nếu daemon đang chạy. Nếu SHA/cấu hình
không đổi, in `UP_TO_DATE` và không ghi host. Máy không có Paseo thì bỏ qua.
`--dry-run` không cập nhật; `--skip-paseo-update` chỉ bỏ qua ở lần chạy đó.
Phiên agent đang mở không tự nạp lại role instruction; mở phiên mới.

Local policy hiện thêm usage report và can thiệp bế tắc Lead–Peer cho heartbeat
Supervisor. Preview in `EFFECTIVE heartbeat_usage_report=True` và
`EFFECTIVE heartbeat_stall_intervention=True`; sau apply, mở Supervisor mới và dùng
`slp-budget.py --root-agent "$PASEO_AGENT_ID"` để xem tổng → role → session.
Script chỉ đọc bộ đếm, không cài plugin hard gate. Plugin
`slp-governor-plugin/` là một gói trusted/unsandboxed riêng và **không được
bootstrap hoặc installer tự kích hoạt**; cần pilot và phê duyệt riêng như
[OPERATIONS.md](OPERATIONS.md) mô tả.

Nếu upstream đổi permission/contract mà Windows adapter chưa hỗ trợ, bootstrap
báo lỗi sau khi phần project đã được cài, còn cấu hình Paseo cũ được giữ hoặc
rollback. Không có việc chạy script từ GitHub; updater chỉ tải dữ liệu role và
protocol theo SHA đã xác định. Bản cập nhật có thể thay toàn bộ profile host.

## Cài hoặc kiểm tra thủ công

Yêu cầu Windows native, Python 3.12+, Paseo Desktop/CLI và Codex CLI đã đăng
nhập. Model/effort của overlay tại commit được chọn phải có trong catalog Codex
trên máy. Từ **Git Bash tại project root**:

```bash
python .agent-toolkit/paseo/install-codex-room-windows.py
python .agent-toolkit/paseo/install-codex-room-windows.py --apply --reload
```

Trên máy dùng nvm4w, nếu Git Bash không thấy Codex, thêm thư mục `nodejs` vào
`PATH` trước khi chạy, ví dụ `export PATH=/c/nvm4w/nodejs:$PATH`. Lệnh đầu
chỉ preview và in quyền hiệu lực (`EFFECTIVE ...`). Lệnh sau backup host, tải
năm tài sản từ commit ghim của [`codex-room-setup`](https://github.com/hoangnb24/codex-room-setup),
cài ba runtime, **thay toàn bộ Agent Profiles hiện có** bằng đúng ba profile,
gỡ alias SLP Claude cũ và reload Paseo. Nếu daemon đang tắt, bỏ `--reload` và
khởi động lại daemon sau. Chỉ dùng khi người dùng đã yêu cầu thay profile host.
`full-access` và `approval_policy=never` là chính sách role
nguồn; nêu rõ trước khi cài. Thu hẹp quyền theo vai trò bằng
`local-policy.toml`, theo các bước và smoke test trong
[OPERATIONS.md](OPERATIONS.md); không sửa tay file đã sinh. Dùng `--source
latest` chỉ khi muốn nhận thay đổi upstream: bộ cài in `UPSTREAM_CHANGED` và
yêu cầu `--accept-upstream-changes` sau khi bạn đã đọc các file đổi.

Trên host kiểm ngày 2026-10-02, hai block hẹp quyền vẫn để comment: Supervisor
`workspace-write` không hoàn thành write probe và bị chặn Paseo tools; Peer
`workspace-write` không đọc được shared protocol bắt buộc nằm ngoài sandbox.
Đây là kết quả acceptance, không phải việc cài thiếu. Chỉ bật lại khi role
contract hoặc provider đổi và chạy lại đủ S1-S7. `paseo_mode_id` chỉ nhận
`auto`, `auto-review`, `full-access`; nó không biến thành sandbox `read-only`.

Kiểm tra ba `codex-*` alias bằng `paseo provider diagnostic <alias> --json` và
mở phiên mới cho từng role. Tìm đường dẫn backup trong output `APPLY_OK`.
Trong checkout MMO, source chính thức nằm ở
`MMO-Tool/github-agent-toolkit/paseo/`; bản được bootstrap vào project tự đủ để
cài và không phụ thuộc checkout đó. Xem [OPERATIONS.md](OPERATIONS.md) để kiểm
tra chi tiết và rollback.

Nếu runtime cũ báo `duplicate key` tại `[features]`, nguyên nhân là config gốc
đã tạo bảng `features` bằng dotted key nhưng launcher cũ còn khai báo lại bảng
đó. Không sửa riêng file generated trong `.codex-runtime`. Cập nhật toolkit,
chạy lại launcher với `--sync-only` cho cả ba role, rồi kiểm từng `CODEX_HOME`
bằng `codex features list`. Launcher hiện giữ dotted-key style khi bảng đã tồn
tại ngầm và regression test parse output bằng `tomllib`.

## Cập nhật Codex CLI và model catalog

Paseo không giữ một bản Codex riêng: ba launcher dùng Codex CLI cài toàn máy.
Trên Windows cài bằng npm, cập nhật theo lệnh chính thức rồi kiểm version:

```bash
npm install -g @openai/codex@latest
codex --version
```

Sau đó chạy installer ở chế độ preview. Installer đọc catalog sống bằng
`codex debug models` và dừng nếu một model/effort đã cấu hình chưa tồn tại.
Reload Paseo rồi mở session mới; session đang mở không đổi model/runtime.

Catalog mới **không tự thêm** model vào menu Paseo. Danh sách hiển thị do
`ROLE_OPTIONS` trong `install-codex-room-windows.py` sở hữu. Muốn đưa một model
mới vào Lead/Peer/Supervisor: thêm lựa chọn có chủ đích, cập nhật test catalog,
chạy toàn bộ suite, preview, rồi mới `--apply --reload`. Không thêm model trước
khi CLI đã có nó, vì phép kiểm catalog sẽ chặn toàn bộ apply.

Không dùng file tám profile hoặc script merge Phase 1 nếu chúng còn sót từ một
checkout cũ; chúng sẽ tạo lại cấu hình trái chuẩn ba role.
