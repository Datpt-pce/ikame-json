---
title: "Kiểm định nghiên cứu Lottie JSON in-app"
date: 2026-10-05
tags:
  - technology
  - lottie
  - validation
domain: Technology
status: reviewed
related:
  - "[[lottie-json-layer-to-developer-handoff|Lottie JSON cho in-app: từ layer thiết kế đến bàn giao developer]]"
  - "[[lottie-runtime-compatibility|Lottie Runtime Compatibility]]"
---

## Tóm tắt

Story `LOTTIE-LIB-001` tạo một guide chuyên sâu, năm term notes và hai index update cho workflow nhận layer → dựng After Effects → export Lottie JSON/dotLottie → QA → bàn giao developer. Nghiên cứu ưu tiên specification, source code và tài liệu first-party của Lottie Animation Community, Airbnb, LottieFiles và Adobe.

## Acceptance Criteria

- [x] Phân biệt format Lottie, exporter Bodymovin, nền tảng LottieFiles, container dotLottie và runtime/player.
- [x] Có contract đầu vào với dev trước khi animate.
- [x] Có workflow cho PSD, AI/SVG và Figma; composition, text/font, raster asset, export và tối ưu.
- [x] Có ma trận QA structure, feature, visual, behavior, runtime/device, performance và accessibility.
- [x] Có template gói handoff, troubleshooting, checklist hằng ngày và ba ví dụ tăng dần độ khó.
- [x] Dữ kiện và khuyến nghị/suy luận được tách rõ; claim quan trọng có nguồn chính thức gần nội dung.
- [x] Wiki-link, frontmatter, required headings, MOC và whitespace được kiểm tra.

## Validation Evidence

| Kiểm tra | Kết quả | Phạm vi |
| --- | --- | --- |
| Frontmatter và cấu trúc bắt buộc | PASS | 1 guide + 5 term notes |
| Ba ví dụ cơ bản/trung cấp/nâng cao | PASS | spinner; onboarding đa ngôn ngữ; reward đa runtime |
| Wiki-link resolution | PASS | 8 file tác vụ được kiểm; 0 target hỏng |
| MOC-Library | PASS | đúng 1 row cho mỗi term mới |
| Nguồn | PASS | LAC, Airbnb, LottieFiles và Adobe; không dùng blog bên thứ ba làm căn cứ |
| Markdown whitespace | PASS | `git diff --check` không báo lỗi nội dung |
| Dung lượng | PASS | guide khoảng 5.400 từ; toàn bộ 6 note kiến thức khoảng 6.800 từ |

## Giới hạn kiểm chứng

- Chưa có layer/AEP hoặc JSON thực của người dùng, nên chưa thể audit path, asset, warning, file size hay render cụ thể.
- Chưa chạy After Effects/LottieFiles plugin, app build, iOS/Android device hoặc browser renderer với một artifact thật.
- Bảng feature và runtime thay đổi theo release; guide bắt buộc pin player/version/renderer và test lại thay vì coi note là compatibility guarantee vĩnh viễn.
- Ngưỡng KB, frame time, số instance và thiết bị thấp nhất phải do từng dự án chốt; nghiên cứu không bịa một budget chung.

## Nguồn

- [[lottie-json-layer-to-developer-handoff|Lottie JSON cho in-app: từ layer thiết kế đến bàn giao developer]].
- [[lottie-animation|Lottie Animation]].
- [[bodymovin|Bodymovin]].
- [[lottiefiles|LottieFiles]].
- [[dotlottie|dotLottie]].
- [[lottie-runtime-compatibility|Lottie Runtime Compatibility]].
