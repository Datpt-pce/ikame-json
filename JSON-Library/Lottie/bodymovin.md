---
title: "Bodymovin"
date: 2026-10-05
tags:
  - library
  - technology
  - animation
  - after-effects
domain: Technology
type: concept
status: reviewed
related:
  - "[[lottie-animation|Lottie Animation]]"
  - "[[lottiefiles|LottieFiles]]"
  - "[[lottie-runtime-compatibility|Lottie Runtime Compatibility]]"
---

## Định nghĩa

Bodymovin là exporter After Effects nằm trong dự án `lottie-web`, dùng để chuyển composition thành dữ liệu Lottie JSON và asset liên quan. `v` trong JSON Bodymovin thông thường ghi phiên bản exporter; nó không phải cam kết rằng mọi runtime hỗ trợ toàn bộ feature đã xuất.

## Cơ chế / Phạm vi

Exporter duyệt composition, layer, transform, shape, text, precomp, image và keyframe rồi tuần tự hóa thành JSON. Setting có thể ảnh hưởng text/glyph, hidden hoặc guide layer, asset hình, extra composition và payload; lựa chọn đúng phụ thuộc hợp đồng runtime và cách đóng gói của sản phẩm.

## Ý nghĩa thực tế

Bodymovin biến được animation thành JSON không đồng nghĩa animation đã sẵn sàng production. Cần preview, đọc warning/report, kiểm feature theo player mục tiêu, tối ưu và test thiết bị thật trước khi bàn giao.

## Ví dụ

Layer Illustrator chưa đổi sang shape có thể được xuất như image cùng thư mục asset. Đổi bằng `Create Shapes from Vector Layer`, dọn path/group thừa và bỏ layer nguồn khỏi comp giúp giữ vector, nhưng kết quả vẫn phải so hình sau export.

## Liên kết

- [[lottie-animation|Lottie Animation]] — định dạng đầu ra.
- [[lottiefiles|LottieFiles]] — plugin/workspace khác trong cùng hệ sinh thái bàn giao.
- [[lottie-runtime-compatibility|Lottie Runtime Compatibility]] — kiểm đầu ra theo target thực.

## Nguồn

- [airbnb/lottie-web README](https://github.com/airbnb/lottie-web/blob/master/README.md)
- [Airbnb Lottie — After Effects guide](https://github.com/airbnb/lottie/blob/master/after-effects.md)
- [airbnb/lottie-web — JSON animation schema](https://github.com/airbnb/lottie-web/blob/master/docs/json/animation.json)
