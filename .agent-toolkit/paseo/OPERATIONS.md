# Vận hành Codex Room SLP trên Windows native

Quy trình này đã chạy với Paseo Desktop 0.9.2, Codex CLI 0.158.0 và Python
3.12.7 ngày 2026-09-29. Bộ cài dùng đúng ba Agent Profile: Supervisor, Lead,
Peer. Chế độ cài thủ công mặc định ghim nguồn vai trò ở commit
[`3481290`](https://github.com/hoangnb24/codex-room-setup/tree/348129092cb1bf92176f062bca0ca0ddda3cfbfe).

## Điều kiện

- Windows native, Python 3.12+, Paseo Desktop/CLI, Codex CLI đã đăng nhập.
- `%USERPROFILE%\.codex\config.toml`, `auth.json` tồn tại. Nếu có `skills\`
  hoặc `plugins\`, runtime chia sẻ chúng với Codex home gốc.
- Catalog Codex có các model và mức reasoning của cả overlay nguồn và danh sách
  lựa chọn: Supervisor `gpt-5.6-sol/medium`; Lead `gpt-5.6-sol/high|xhigh`
  hoặc `gpt-6-sol/medium`; Peer `gpt-5.6-terra/high|xhigh|max`.
- Ba role chạy `full-access`, approval `never` theo overlay nguồn. Supervisor
  và Lead thấy Paseo tools; Peer không thấy.

Kiểm tra `paseo`, `codex`, `python` trên Windows native và đăng nhập Codex bằng
`codex login` theo giao diện chính thức trước khi chạy installer.

## Tự cập nhật qua github-agent-toolkit

Trên Windows đã cài Paseo, `MMO-Tool/github-agent-toolkit/bootstrap.py` tự lấy
commit `main` mới nhất của repo nguồn rồi chạy updater sau khi project được khởi
tạo. Updater kiểm role, toàn bộ model/effort trong Codex catalog, backup và thay ba
profile/runtime; daemon đang chạy được reload. Nếu không đổi, `UP_TO_DATE` không
ghi host. `--dry-run` và `--skip-paseo-update` không chạy updater; máy không có
Paseo được bỏ qua. Nếu upstream đổi permission/contract ngoài phạm vi adapter
Windows, updater dừng và giữ hoặc khôi phục cấu hình cũ. Phiên agent đang mở
không tự đổi role.

## Xem trước và cài thủ công

Mở Git Bash tại thư mục checkout MMO. Trên máy hiện tại, cần thêm đường dẫn
Node/Codex vào `PATH` của Git Bash; sửa theo nơi cài Node của bạn:

```bash
export PATH=/c/nvm4w/nodejs:$PATH
python MMO-Tool/github-agent-toolkit/paseo/install-codex-room-windows.py
python MMO-Tool/github-agent-toolkit/paseo/install-codex-room-windows.py --apply --reload
```

Thêm `--source latest` vào cả hai lệnh để dùng commit `main` mới nhất, giống
toolkit bootstrap. Không có cờ này, bộ cài dùng commit ghim đã kiểm chứng.

Lệnh đầu chỉ in kế hoạch. Lệnh sau tải năm tài sản từ commit ghim, kiểm SHA-256,
backup cấu hình host và các file bị quản lý vào
`%USERPROFILE%\.codex-room-backups\windows-<timestamp>-<pid>`, cài launcher,
sinh ba runtime, thay **toàn bộ** `daemon.agentProfiles` bằng đúng ba profile,
thay ba alias Codex SLP và gỡ ba alias Claude SLP cũ, rồi `paseo reload`.
Những provider khác và phần cấu hình Paseo khác được giữ. Lệnh không chạm
`%USERPROFILE%\.codex\config.toml` hay credential.

Không chạy `install --apply` Bash của repo nguồn trực tiếp trên Windows native:
source giả định POSIX symlink và đường dẫn macOS. Bộ cài này dùng hardlink cho
file chia sẻ và junction cho `skills/`, `plugins/`, vì file symlink thường cần
quyền admin trên Windows. Ba runtime riêng ở `%USERPROFILE%\.codex-runtime\`.

## Kiểm tra

```powershell
$Paseo = "$env:LOCALAPPDATA\Programs\Paseo\resources\bin\paseo.cmd"
& $Paseo daemon status --json
& $Paseo provider diagnostic codex-supervisor --json
& $Paseo provider diagnostic codex-lead --json
& $Paseo provider diagnostic codex-peer --json
```

Trong Paseo, Settings → host → Agents → Agent profiles phải có đúng ba tên
`Codex Room Supervisor`, `Codex Room Lead`, `Codex Room Peer`. Profile lưu
lựa chọn mặc định (Lead High, Peer High); khi tạo phiên có thể đổi model và
reasoning trong danh sách của provider tương ứng. Mở phiên mới để nhận config
mới; profile edit không cập nhật session đang chạy.
Ngày 2026-09-29, cả ba alias đã báo `Ready` và ba phiên `paseo agent run` riêng
đều hoàn thành smoke prompt.

## Cấu trúc và vận hành

```text
Paseo profile/alias → Python role launcher → sync runtime role → Codex app-server
                                            ├─ config/catalog/session riêng
                                            └─ auth, skills, plugins dùng chung
```

Launcher merge `~/.codex/config.toml` với overlay vai trò của nguồn, ghim
`agents.enabled=false`, `features.multi_agent=false` và
`features.multi_agent_v2=false`, đồng thời xoá metadata native multi-agent khỏi
model catalog runtime. Khi config gốc đã dùng dotted key như
`features.context_management.experimental_mode`, launcher thêm các cờ cùng
dạng dotted key ở vùng top-level thay vì khai báo lại `[features]`. Điều phối
SLP dùng Paseo tools của Supervisor/Lead.

Mỗi lần mở agent, launcher chỉ thay atomically file runtime khi nội dung sinh ra
thực sự đổi. Nếu Codex app-server khác đang giữ catalog mở nhưng nội dung vẫn
giống nhau, launcher dùng lại file hiện có để tránh `WinError 5`. Nếu nội dung
đã đổi mà file còn bị giữ, launcher vẫn dừng thay vì âm thầm dùng catalog cũ;
đóng phiên giữ file rồi thử lại.
Hợp đồng quyền sở hữu và bàn giao nằm ở
[`WORKSPACE_PROTOCOL.md`](https://github.com/hoangnb24/codex-room-setup/blob/348129092cb1bf92176f062bca0ca0ddda3cfbfe/home/.config/codex-room/workflow/WORKSPACE_PROTOCOL.md)
được cài vào `%USERPROFILE%\.config\codex-room\workflow\`.

Khi chuyển quyền sở hữu giữa hai Lead, dùng đúng chuỗi bàn giao:
PREPARE (successor ở
`STANDBY`) → READY → RELEASE → HANDOFF_ACCEPT.

### Sửa runtime cũ báo `duplicate key` tại `[features]`

Runtime được sinh bởi launcher cũ có thể đồng thời chứa dotted key
`features.*` ở đầu file và bảng `[features]` ở cuối file. Không sửa riêng từng
file trong `.codex-runtime` vì lần sync kế tiếp sẽ ghi đè. Cập nhật launcher,
chạy lại `--sync-only` cho `supervisor`, `lead`, `peer`, rồi xác nhận từng
`CODEX_HOME` bằng `codex features list`. Regression test dùng `tomllib` bảo đảm
output merge parse được trước khi phát hành.

Hardlink chia sẻ auth theo inode hiện tại. Nếu Codex thay `auth.json` bằng cách
ghi đè nguyên file, launcher phát hiện hardlink lệch và dừng; cần xử lý đường
link sau khi kiểm tra credential hiện hành. Không copy credential vào repo.

## Rollback

Dừng phiên mới đang dùng ba alias. Tìm đường dẫn `APPLY_OK backup=...` trong
output cài đặt. `manifest.json` ghi ánh xạ từng file trước khi thay. Khôi phục
`file-00` về `%USERPROFILE%\.paseo\config.json`, sau đó `paseo reload`.
Các file được sinh riêng ở `.codex-runtime` và `.config\codex-room` có thể giữ
để kiểm tra; không chứa bản copy credential (auth dùng hardlink).

Source được duy trì tại `MMO-Tool/github-agent-toolkit/paseo/`. Các
script/template tám profile Phase 1 đã bị loại bỏ; không khôi phục hoặc chạy lại
chúng vì sẽ tạo cấu hình trái chuẩn ba role.
