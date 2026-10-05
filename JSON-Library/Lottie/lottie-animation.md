---
title: "Lottie Animation"
date: 2026-10-05
tags:
  - library
  - technology
  - animation
  - lottie
domain: Technology
type: concept
status: reviewed
related:
  - "[[bodymovin|Bodymovin]]"
  - "[[dotlottie|dotLottie]]"
  - "[[lottie-runtime-compatibility|Lottie Runtime Compatibility]]"
  - "[[design-handoff|Design Handoff]]"
---

## Định nghĩa

Lottie là định dạng dữ liệu JSON mô tả animation vector theo composition, layer, asset và property có thể keyframe. Player đọc dữ liệu này rồi render ở runtime; file Lottie không phải video đã raster sẵn và cũng không tự bảo đảm mọi player cho kết quả giống nhau.

## Cơ chế / Phạm vi

Animation gốc chứa kích thước `w`/`h`, frame rate `fr`, vùng phát `ip`–`op`, `layers`, `assets` và có thể có `markers`. Layer có type, thời gian hiện diện, transform, mask/matte và nội dung riêng; property tĩnh dùng giá trị trực tiếp, còn property động dùng chuỗi keyframe.

## Ý nghĩa thực tế

Lottie phù hợp cho icon, illustration và microinteraction cần scale, tải nhẹ và điều khiển bằng code. Tính tương thích thực tế là giao của feature trong file với platform, player, phiên bản và renderer mục tiêu; phải kiểm theo [[lottie-runtime-compatibility|ma trận runtime]] thay vì chỉ preview trong công cụ thiết kế.

## Ví dụ

Một animation thành công 60 frame ở 30 fps có thể chứa shape checkmark, hai marker `intro` và `settle`, rồi được dev phát theo segment. Nếu animation dựa vào một matte hoặc text feature không có ở runtime mục tiêu, JSON vẫn hợp lệ nhưng hình có thể sai.

## Liên kết

- [[bodymovin|Bodymovin]] — exporter phổ biến chuyển composition After Effects thành Lottie JSON.
- [[dotlottie|dotLottie]] — container đóng gói một hay nhiều Lottie cùng asset.
- [[lottie-runtime-compatibility|Lottie Runtime Compatibility]] — hợp đồng tương thích và QA đa player.
- [[design-handoff|Design Handoff]] — bàn giao hành vi, asset và bằng chứng cho developer.

## Nguồn

- [Lottie Animation Format Specification](https://lottie.github.io/lottie-spec/latest/)
- [Lottie specification — Composition](https://lottie.github.io/lottie-spec/latest/specs/composition/)
- [Lottie specification — Layers](https://lottie.github.io/lottie-spec/latest/specs/layers/)
