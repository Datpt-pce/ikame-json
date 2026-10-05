# Bộ kiến thức Lottie JSON

Đây là snapshot tự chứa của bộ tài liệu Lottie JSON đã được review trong
`Datpt-pce/mmo`, commit `9dfe3f347dec8b495adb24a43fbbacb9ba66906c`, lấy ngày
2026-10-05. Các file nội dung được giữ nguyên để bảo toàn nguồn, frontmatter và
wiki-link; file này là index dành riêng cho repo `ikame-json`.

## Thứ tự đọc

1. [Lottie JSON cho in-app: từ layer thiết kế đến bàn giao developer](lottie-json-layer-to-developer-handoff.md)
2. [Kiểm định nghiên cứu](lottie-json-research-validation.md)
3. Các khái niệm nền theo nhu cầu:
   - [Lottie Animation](lottie-animation.md)
   - [Bodymovin](bodymovin.md)
   - [LottieFiles](lottiefiles.md)
   - [dotLottie](dotlottie.md)
   - [Lottie Runtime Compatibility](lottie-runtime-compatibility.md)
   - [Design Handoff](design-handoff.md)

Sáu wiki-link cross-domain trong `design-handoff.md` (UI/UX, accessibility,
responsive và product engineering) vẫn là tham chiếu về thư viện MMO gốc và không
được vendor vào đây, vì không thuộc corpus chuyên biệt Lottie JSON. Toàn bộ target
wiki-link Lottie của guide chính đều có mặt trong thư mục này.

## Cách áp dụng

- Trước khi tạo hoặc sửa artifact, chốt platform, player/version, renderer, canvas,
  timing, playback, asset/font strategy, budget và fallback.
- Xem JSON là mô hình dữ liệu animation, không phải video đổi đuôi.
- Kiểm schema/cấu trúc chỉ là một gate; acceptance cuối vẫn cần đúng runtime và
  thiết bị đích.
- Bản optimized phải được regression-test riêng với bản original.
- Bàn giao kèm contract, version/hash, source chỉnh sửa, fallback, QA evidence và
  known limitations phù hợp với phạm vi dự án.

## Đồng bộ nguồn

Nguồn đăng ký vẫn nằm trong
[`knowledge-sources.json`](../../.agent-toolkit/knowledge-sources.json). Khi nguồn
thay đổi, so sánh theo commit và review diff trước khi cập nhật snapshot; không ghi
đè âm thầm lên ghi chú riêng của repo.
