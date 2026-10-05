# JSON-Project/specs/ — Index và quy trình WBS + GTD

Đọc index này trước khi mở, tạo, cập nhật hoặc di chuyển spec. Đây là bản đồ
công việc của dự án; `MASTER.MD` tại project root là quy ước chung cho AI.
Các bảng ban đầu để trống, chỉ thêm công việc thực tế được người dùng giao.

## 1. Phạm vi và cách bắt đầu

- Chỉ mở/làm spec khi yêu cầu nêu tên file hoặc mô tả đủ để xác định đúng spec.
  Dùng index chọn đúng đường dẫn và dependency cần đọc; không tự chọn backlog.
- Tạo spec khi người dùng yêu cầu tạo spec hoặc giao bài toán mới cần theo dõi
  nhiều phiên. Việc nhỏ xử lý theo quy trình hiện có của repository.
- `JSON-Project/specs/` theo dõi outcome, phạm vi và tiến độ. Tài liệu hành vi hiện hành,
  story triển khai, bug log và bằng chứng nằm ở nơi dự án đã quy định; liên kết
  tới chúng. Khi có Harness, dùng intake/story/validation của Harness cho thực thi.
- Spec Done trong Archive chỉ đọc khi cần lịch sử/quyết định được yêu cầu.

## 2. Phân loại theo kết quả

WBS (Work Breakdown Structure) chia công việc theo kết quả cần bàn giao.
GTD (Getting Things Done) xác định hành động tiếp theo làm được ngay.
Phân tầng: Area/Initiative → Project → Deliverable/Work Package → Next Action.

| Loại | Khi dùng | Vị trí / mẫu |
| --- | --- | --- |
| Area | Trách nhiệm liên tục, không có điểm hoàn tất | `Areas/<slug>.md` hoặc folder; [_templates/area.md](_templates/area.md) |
| Initiative | Nhiều project outcome, có governance và mốc riêng | `Initiatives/<slug>/README.md`; [_templates/initiative.md](_templates/initiative.md) |
| Project | Một outcome cần nhiều action, có điểm kết thúc | `Projects/<slug>.md` hoặc folder; [_templates/project.md](_templates/project.md) |
| Project con | Outcome thuộc Initiative | File/folder trong Initiative; dùng cùng mẫu Project |
| Work Package | Kết quả nhỏ nhất có owner và acceptance | Mục/file trong Project; [_templates/work-package.md](_templates/work-package.md) |
| Archive | Nơi lưu project/sub-plan đã Done, không phải loại công việc | `Archive/`; giữ nguồn gốc và bằng chứng |

Khi một Work Package được thực thi theo Codex Room Supervisor–Lead–Peer, chi
tiết từng vòng SLP (ma trận, hash candidate, reject theo lớp lỗi, evidence)
**không** ghi trong `JSON-Project/specs/`. Nó nằm ở một story riêng của dự án (ví dụ
`JSON-Project/<project-slug>/docs/stories/<ID>/`), theo quy tắc ở
`.agent-toolkit/paseo/SLP-WORKFLOW.md` mục 8.1. `JSON-Project/specs/`
chỉ nhận một dòng checklist khi story đó ACCEPT hoặc dừng ở REJECT/on-hold,
đúng định dạng checklist đã có trong `work-package.md`/`project.md`.

Dùng tên kebab-case mô tả nội dung. Spec mới nằm trong nhóm phù hợp; root
`JSON-Project/specs/` dành cho index. `_templates/` chỉ chứa mẫu, không đưa vào bảng tiến độ.
Area không hoàn tất như Project: khi có kết quả hữu hạn, tạo Project liên kết Area.

## 3. Complexity gate

Chấm 1 điểm cho mỗi câu có và ghi lý do vào spec:

1. Có từ hai owner/team?
2. Có dependency bên ngoài?
3. Có từ ba deliverable độc lập?
4. Sai sót gây chi phí lớn hoặc khó đảo ngược?
5. Scope/giải pháp còn bất định đáng kể?
6. Kéo dài quá hai tuần hoặc qua nhiều mốc duyệt?

| Tổng | Cấu trúc |
| --- | --- |
| 0–1 | Một file phẳng |
| 2–3 | WBS nhẹ: vài section hoặc 2–3 file |
| 4–6 | Folder WBS theo deliverable; cân nhắc Initiative khi có nhiều outcome |

**100% Rule:** các phần con phủ hết phạm vi đã chọn của phần cha, kể cả kiểm thử,
tài liệu và bàn giao; mỗi kết quả có một nơi chịu trách nhiệm, tránh đếm trùng.
Đặt tên theo kết quả cần tồn tại, không theo danh sách hoạt động mơ hồ. Mỗi Work
Package có owner, đầu ra, acceptance, dependency và cách chứng minh hoàn tất.
Gate này quyết định độ chi tiết tài liệu; rủi ro thực thi vẫn theo quy tắc dự án.

## 4. Trạng thái và Next Action

Mỗi Project/Work Package có `Project Status` gần đầu tài liệu:

```text
Outcome: <kết quả có thể xác nhận đã đạt>
State: Active | Waiting For | Someday/Maybe | Done
Next Action: <động từ + đối tượng cụ thể + dấu hiệu kết thúc>
Waiting For: <ai/cái gì + điều kiện được gỡ chặn, chỉ khi đang chờ>
Updated: <YYYY-MM-DD>
```

- **Active:** luôn có ít nhất một Next Action thực hiện được ngay. Ví dụ giả định:
  “Chạy kiểm tra hợp đồng cho endpoint đã chọn; xong khi các case acceptance đạt.”
- **Waiting For:** ghi bên/phụ thuộc đang chờ và điều kiện tiếp tục; bỏ Next Action
  phụ thuộc đang bị chặn. Nếu còn việc độc lập làm ngay, giữ Active và ghi dependency.
- **Someday/Maybe:** chưa chọn làm; ghi điều kiện xem xét lại, không giả lập action
  đang thực thi. Nếu chưa có action khả thi cũng không có blocker cụ thể, dùng state này.
- **Done:** outcome/acceptance đã đạt và có evidence; bỏ Next Action/Waiting For.

State là metadata, không di chuyển folder mỗi lần đổi trạng thái. Chỉ archive khi
đủ điều kiện mục 7. Khi chạm spec cũ, bổ sung field thiếu, giữ lịch sử/bằng chứng hợp lệ.

## 5. Index hiện tại

### Areas

| Spec | Trách nhiệm liên tục | Project liên quan / lần rà soát tới |
| --- | --- | --- |

### Initiatives

| Spec | Outcome | State | Project con đang active | Next Action / Waiting For |
| --- | --- | --- | --- | --- |

### Projects

| Spec | Outcome | State | Next Action / Waiting For |
| --- | --- | --- | --- |

Project con đã được quản lý trong index của Initiative thì chỉ cần liên kết từ
dòng Initiative ở đây; cập nhật cả index con khi thay đổi tiến độ.

### Archive

| Spec | Outcome đã đạt / evidence | Xuất xứ / spec kế tiếp |
| --- | --- | --- |

### Điểm giao nhau và dependency

| Các spec liên quan | Phần dùng chung / nguồn chính | Thứ tự hoặc điều kiện | Kiểm tra khi thay đổi |
| --- | --- | --- | --- |

## 6. Vòng làm việc và bàn giao

1. Capture/Clarify: xác định spec từ yêu cầu, outcome và scope được chọn.
2. Organize: đọc index, kiểm tra dependency và việc đang dở; với spec mới chấm
   gate, chọn template/vị trí, điền status và thêm dòng index.
3. Engage: làm Next Action theo quy trình repository; cập nhật `[x]` chỉ khi có
   evidence. Phân biệt đã viết tài liệu, đã code, đã test, đã deploy.
4. Reflect: sau mỗi phần việc, cập nhật status/checklist ngay trong spec, rồi
   đồng bộ dòng MASTER và index Initiative liên quan. Ghi ngày, evidence và blocker.
5. Bàn giao ngắn **Progress / Decisions / Next Steps**, giữ trạng thái mới nhất;
   quyết định bền vững liên kết đến tài liệu quyết định của dự án.

Review khi người dùng yêu cầu hoặc mở lại công việc; không tạo lịch review cá
nhân cố định. Một spec “Active” chỉ có tiêu đề, không action, là chưa sẵn sàng.

## 7. Archive có bằng chứng

Chỉ archive khi outcome và toàn bộ acceptance trong scope đạt, không còn checkbox
`[ ]` mở. Đọc checklist và evidence, không chỉ tin nhãn “hoàn tất”. Việc ngoài
scope phải được ghi rõ, liên kết công việc kế tiếp nếu đã được giao; không tự hạ
acceptance hoặc bỏ việc bắt buộc để chuyển Done.

1. Kiểm tra nội dung và cập nhật Done cùng bằng chứng.
2. Di chuyển file/folder vào `Archive/` theo workflow repository (`git mv` nếu đã
   tracked); với project con thêm tiền tố Initiative khi cần giữ nguồn gốc.
3. Sửa cả link trỏ vào lẫn link tương đối bên trong file đã di chuyển; tìm các
   tham chiếu cũ trên repository và kiểm tra đường dẫn sau khi sửa.
4. Chuyển dòng index sang Archive, cập nhật index cha và dependency liên quan.

Tính năng tiếp theo tạo/liên kết spec đang hoạt động thay vì kéo dài spec đã Done.
