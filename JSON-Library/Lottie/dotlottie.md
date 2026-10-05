---
title: "dotLottie"
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
  - "[[lottie-animation|Lottie Animation]]"
  - "[[lottiefiles|LottieFiles]]"
  - "[[lottie-runtime-compatibility|Lottie Runtime Compatibility]]"
---

## Định nghĩa

dotLottie là container nén có đuôi `.lottie`, đóng gói một hoặc nhiều animation Lottie cùng `manifest.json` và các tài nguyên như image, font, theme hoặc state machine theo phiên bản specification.

## Cơ chế / Phạm vi

dotLottie 2.0 là ZIP Deflate với MIME type `application/zip+dotlottie`; cấu trúc cốt lõi gồm `manifest.json`, thư mục animation `a/` và các thư mục tùy chọn cho image, font, theme, state machine. dotLottie 1.0 dùng layout khác, nên version container là một phần của contract.

## Ý nghĩa thực tế

Container giúp gom asset, tái sử dụng tài nguyên và phân phối nhiều animation trong một file. Không nên chọn `.lottie` chỉ vì nhỏ hơn: dev phải xác nhận player/runtime đang dùng hỗ trợ đúng version và feature của package.

## Ví dụ

Một bộ ba trạng thái nút `idle`, `loading`, `success` có thể đóng gói thành một `.lottie` với ba JSON và asset dùng chung. Nếu app hiện tại chỉ nhận JSON Bodymovin riêng lẻ, bàn giao `.lottie` sẽ tạo lỗi tích hợp dù preview trên LottieFiles đúng.

## Liên kết

- [[lottie-animation|Lottie Animation]] — dữ liệu animation nằm trong container.
- [[lottiefiles|LottieFiles]] — công cụ có thể export, preview và handoff JSON/dotLottie.
- [[lottie-runtime-compatibility|Lottie Runtime Compatibility]] — kiểm version container và player.

## Nguồn

- [dotLottie Specification](https://www.dotlottie.io/spec/)
- [dotLottie 2.0 Specification](https://www.dotlottie.io/spec/2.0/)
- [dotLottie 1.0 Specification](https://www.dotlottie.io/spec/1.0/)
