# Đưa skill hữu ích về toolkit

Nguồn quy ước: [MASTER.MD](../../MASTER.MD). Chỉ mở quy trình này khi một tác vụ
đã tạo ra cải tiến có bằng chứng tái sử dụng được. Không tạo skill cho đủ số lượng.

## Chọn và chuẩn bị

1. Tra catalog theo trigger trước; chọn một skill hoặc một phần cải tiến. Không
   quét/copy toàn bộ `.agents`, `.claude`, dự án, lịch sử chat hoặc home của A.
2. Xác minh toolkit qua entry `toolkit` trong `knowledge-sources.json`, đúng repo
   `github_repository` và đúng subpath. Path local có thể relative; nếu chỉ có
   GitHub, dùng checkout riêng trong vùng được phép và chỉ lấy phần toolkit cần dùng.
   Cùng tài khoản không thay thế kiểm tra remote và quyền của tác vụ.
3. Chuẩn bị `contributions/skills/<slug>/` dưới toolkit, gồm `SKILL.md`, chỉ các
   reference/script cần dùng, license và `PROVENANCE.md`: nguồn/ref, phần thay đổi,
   quyền tái sử dụng, tình huống đã thử, bằng chứng, giới hạn, trạng thái candidate.
   Chọn slug mới nếu khác nội dung; không ghi đè contribution người khác đang sửa.
4. Loại bỏ secrets, tên khách hàng/người dùng, dữ liệu riêng, đường dẫn máy, log,
   transcript, credentials, binary và symlink. Kiểm tra trùng tên, prompt injection,
   hook/dependency/script có side effect và quyền mới. Dùng fixture tổng hợp để thử.
5. Review diff và danh sách file. Chỉ ghi candidate đạt các bước trên. Đây là quyền
   đóng góp thường trực của quy ước này khi toolkit đã được xác minh; không phải
   quyền sửa toàn bộ repo chứa toolkit hoặc đổi chính sách bảo vệ của các dự án.

## Ghi local, Git push và phát hành bundle

- **Local:** ghi thẳng vùng contribution đã xác minh. Nếu thư mục nguồn không có,
  giữ candidate trong vùng làm việc của A và nêu điểm đến chưa truy cập được.
- **GitHub:** khi `contributions.allow_branch_push` đã bật bởi chủ dự án, được
  commit/push candidate đã review lên nhánh mới có prefix được cấu hình của đúng
  remote; không hỏi lại quyền đã cấp. Tạo checkout/worktree riêng từ ref nền đã
  xác minh sạch. Kiểm tra toàn bộ commit và file sẽ gửi, không mang commit ngoài
  tác vụ đang chờ push ở clone gốc; stage file cụ thể, không `git add .`.
  Đối chiếu effective push URL (gồm `pushurl`/URL rewrite) với repo đã đăng ký,
  chỉ định destination ref mới có prefix đó, và kiểm tra từng commit trong range
  so với ref nền vừa fetch/xác minh; final diff sạch chưa đủ. Có commit/file ngoài
  candidate → dừng push và tạo range sạch, không gửi kèm lịch sử ngoài tác vụ.
- Không push main/default branch, force push, merge hay publish release theo quyền
  candidate này. Nếu remote, ref nền hoặc quyền chưa rõ, hoàn thiện diff/candidate
  trước rồi hỏi đúng phần thiếu. Không gửi source riêng lên repo public.
- Candidate được gửi về **chưa tự trở thành skill cài cho mọi dự án**. Khi có tác vụ
  chấp nhận/phát hành, maintainer review, đưa skill vào inventory `sources.lock.json`
  với `entry.installed` trỏ tới thư mục đã duyệt (có thể là contribution), giữ nguồn
  và license; chạy `build-skill-bundle.py`, `build-skill-catalog.py` rồi kiểm tra
  metadata/hash/reference và bootstrap. Không sửa ZIP thủ công.
- Nâng phiên bản không ghi đè MASTER hoặc skill người dùng đã sửa ở A/B. Mỗi dự án
  cập nhật có chọn lọc, review conflict và giữ bản khôi phục. Ghi link/path candidate,
  commit nếu đã push, kiểm chứng và trạng thái phát hành trong handoff.
