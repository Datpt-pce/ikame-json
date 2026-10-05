---
title: "LottieFiles"
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
  - "[[bodymovin|Bodymovin]]"
  - "[[dotlottie|dotLottie]]"
  - "[[design-handoff|Design Handoff]]"
---

## Định nghĩa

LottieFiles là hệ sinh thái công cụ và workspace cho việc tạo, preview, kiểm tra, tối ưu, quản lý phiên bản và bàn giao animation Lottie; đây không phải chính định dạng Lottie và cũng không phải runtime duy nhất mà ứng dụng sẽ dùng.

## Cơ chế / Phạm vi

Plugin After Effects có thể export JSON/dotLottie và preview; workspace cung cấp Feature Support Checker, kiểm trên nhiều player, test mobile, accessibility analyzer và tùy chọn handoff/CDN. Mỗi công cụ chỉ cung cấp một lớp bằng chứng, không thay thế test trong app mục tiêu.

## Ý nghĩa thực tế

Preview đúng trên LottieFiles xác nhận file render đúng trong môi trường đó. Trước production vẫn phải khóa player/version/renderer của dev, kiểm asset path, marker, loop/segment, hiệu năng và fallback trên thiết bị mục tiêu.

## Ví dụ

Designer upload `reward.v3.json`, chạy Feature Support Checker cho các thư viện/version dev đã nêu, test QR trên mobile, rồi gửi version cố định và thông số phát. Nếu dùng Asset CDN, đội sản phẩm còn phải quản lý quota, cache và khả năng asset bị vô hiệu hóa ngoài file source.

## Liên kết

- [[lottie-animation|Lottie Animation]] — format mà hệ sinh thái xử lý.
- [[bodymovin|Bodymovin]] — exporter gốc/khác với thương hiệu nền tảng.
- [[dotlottie|dotLottie]] — định dạng package do hệ sinh thái hỗ trợ.
- [[design-handoff|Design Handoff]] — hợp đồng bàn giao cho developer.

## Nguồn

- [LottieFiles for After Effects](https://help.lottiefiles.com/hc/en-us/articles/4439877810841-getting-started)
- [Feature Support Checker](https://help.lottiefiles.com/hc/en-us/articles/15171713588761-feature-support-checker)
- [Handoff & Embed](https://help.lottiefiles.com/hc/en-us/articles/8704650653593-handoff-embed)
