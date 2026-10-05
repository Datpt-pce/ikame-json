---
title: "Lottie Runtime Compatibility"
date: 2026-10-05
tags:
  - library
  - technology
  - animation
  - compatibility
domain: Technology
type: framework
status: reviewed
related:
  - "[[lottie-animation|Lottie Animation]]"
  - "[[bodymovin|Bodymovin]]"
  - "[[dotlottie|dotLottie]]"
  - "[[design-handoff|Design Handoff]]"
---

## Định nghĩa

Lottie Runtime Compatibility là hợp đồng rằng feature dùng trong animation nằm trong phần giao được hỗ trợ bởi platform, player, phiên bản, renderer và thiết bị mục tiêu, đồng thời đã qua kiểm tra hình ảnh và hiệu năng trong chính môi trường đó.

## Cơ chế

Đánh giá theo tuple `platform + player + version + renderer + minimum device/OS`, rồi lập ma trận từng feature quan trọng: shape/modifier, mask/matte, blend/effect, text/font/glyph, image, 3D, expression, marker, slot/theme và dotLottie version. “Có hỗ trợ” trong một player không suy ra có hỗ trợ ở player khác.

## Ý nghĩa thực tế

Đây là acceptance gate giữa motion designer và developer. LottieFiles Feature Support Checker giúp phát hiện sớm, nhưng production sign-off cần render trong app, test frame/segment/loop seam, asset loading, reduced motion và frame time trên thiết bị đại diện.

## Ví dụ

Một repeater có thể render trên Android, iOS Core Animation và Web nhưng khác ở iOS Main Thread theo ma trận hiện hành. Nếu app iOS ép engine khác, cùng một JSON có thể đổi kết quả; bàn giao phải ghi engine và version đã test thay vì ghi chung “iOS OK”.

## Liên kết

- [[lottie-animation|Lottie Animation]] — file được đánh giá.
- [[bodymovin|Bodymovin]] — exporter và warning là đầu vào, không phải bằng chứng cuối.
- [[dotlottie|dotLottie]] — compatibility còn bao gồm version container.
- [[design-handoff|Design Handoff]] — nơi ghi target, acceptance và bằng chứng.

## Nguồn

- [Airbnb Lottie — Supported features](https://github.com/airbnb/lottie/blob/master/supported-features.md)
- [LottieFiles — Feature Support Checker](https://help.lottiefiles.com/hc/en-us/articles/15171713588761-feature-support-checker)
- [lottie-web — Load animation options](https://github.com/airbnb/lottie-web/wiki/loadAnimation-options)
- [Lottie iOS — Rendering engines](https://github.com/airbnb/lottie/blob/master/ios.md)
