# Paseo SLP cho project dùng toolkit

Khi người dùng muốn chạy nhiều agent qua Paseo, đề xuất chuẩn Windows ở
[`../paseo/SETUP-WINDOWS.md`](../paseo/SETUP-WINDOWS.md). Trên Windows có Paseo,
chạy bootstrap toolkit tự cập nhật cấu hình host từ commit ghim đã duyệt và áp
`paseo/local-policy.toml`; `--paseo-source latest` phải gọi rõ. Chỉ đọc tài
liệu không kích hoạt cập nhật.

SLP quy định quyền sở hữu công việc:

| Vai trò | Trách nhiệm |
| --- | --- |
| Supervisor | Đầu mối với Human, giám sát outcome và chuyển việc kỹ thuật cho Lead. |
| Lead | Chủ sở hữu kỹ thuật duy nhất; giao Peer khi có scope tách được; tích hợp, kiểm tra và accept/reject bằng evidence. |
| Peer | Thực hiện một outcome bounded hoặc review độc lập theo brief; bàn giao candidate và evidence, không tự accept. |

Mỗi moving write scope chỉ có một owner. Lead phải nêu outcome, scope, nguồn
đầu vào đã chốt, cách kiểm tra và điều kiện báo blocker trong brief. Peer không
tự mở rộng scope. Supervisor không nghiệm thu thay Lead. Project `MASTER.MD`,
chỉ dẫn theo folder và skill chuyên môn vẫn áp dụng cho từng vai trò.

Ba profile giữ mặc định: Supervisor `gpt-5.6-sol/medium`, Lead
`gpt-5.6-sol/high`, Peer `gpt-5.6-terra/high`. Khi tạo phiên, Lead có thể chọn
`gpt-5.6-sol/xhigh` hoặc `gpt-6-sol/medium`; Peer có thể chọn
`gpt-5.6-terra/xhigh|max` theo độ khó. Kiểm tra catalog sống trước khi chọn;
không thay ngầm khi thiếu model.
Profile mới chỉ có hiệu lực với session mới. Paseo cung cấp agent lifecycle và
orchestration tools; nó không tự thực thi quy tắc ownership SLP.

Hợp đồng chi tiết được cài tại
`%USERPROFILE%\.config\codex-room\workflow\WORKSPACE_PROTOCOL.md` từ commit
nguồn ghim. Đọc file đó trước khi điều phối thực tế. Bộ cài thay toàn bộ danh
sách Agent Profiles. Overlay nguồn dùng `full-access`/approval `never`; quyền
hiệu lực của từng vai trò do `paseo/local-policy.toml` quyết định và được in ở
bước preview. Bản phân phối chỉ bật heartbeat; hai role block để comment sau
smoke Windows 2026-10-02 không đạt. Không mô tả role là sandboxed nếu preview
vẫn in `danger-full-access`. Chỉ chạy khi người dùng chạy bootstrap trên host
có Paseo hoặc gọi bộ cài thủ công.

## Trước khi viết source

Vai trò rõ không ngăn được chuỗi reject. Với công việc nhạy cảm về bảo mật,
lifecycle hoặc dữ liệu, làm theo
[`../paseo/SLP-WORKFLOW.md`](../paseo/SLP-WORKFLOW.md):

1. Human duyệt mô hình đe doạ và ngân sách. Audit không tự nâng mức bảo vệ.
2. Lead cân ít nhất hai phương án và thử primitive bắt buộc trên máy đích.
3. Hai Peer làm nhiệm vụ review không ghi source để audit **ma trận chấp
   nhận**, rồi Lead đóng băng nó.
4. RED theo ma trận; writer chỉ chạy focused test; Lead chạy bộ kiểm đầy đủ một
   lần cho mỗi hash; audit độc lập chỉ sau khi Lead soát đủ từng dòng.
5. Reject theo lớp lỗi. Cùng khu vực bị reject hai lần thì mở lại thiết kế; lần
   thứ ba thì báo Human.
