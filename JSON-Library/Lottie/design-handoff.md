---
title: "Design Handoff"
date: 2026-09-13
tags: [library, product, uiux]
domain: Product
type: concept
status: reviewed
related:
  - "[[design-system]]"
  - "[[interaction-design]]"
  - "[[responsive-design]]"
  - "[[web-accessibility]]"
  - "[[product-engineering-beyond-system-design]]"
  - "[[MOC-UIUX|MOC: UI/UX]]"
---

## Định nghĩa

Bàn giao thiết kế chuyển quyết định và bằng chứng thành thông tin developer có thể hiện thực: requirement, component, layout, state, nội dung và acceptance. Đây là hợp đồng hành vi chứ không chỉ là ảnh.

## Ý nghĩa thực tế

Map requirement_id → screen/board_id → component/token → code path → phép thử. Chỉ ghi ID và export thật. Tách phần xác nhận trong Penpot, phần code đã kiểm, phần cần user test; prototype không chứng minh database hay permission.

## Ví dụ

Màn hình đặt lịch bàn giao gồm board desktop/mobile, lỗi lịch vừa bị người khác chọn, trạng thái đang gửi, quy tắc focus và test chống gửi trùng. Backend contract phải lấy từ dự án.

## Liên kết

- [[design-system|Design System]] — chuẩn hóa và bảo trì quy tắc cùng component dùng lại.
- [[interaction-design|Interaction Design]] — mô tả hành động, chuyển trạng thái và đường phục hồi.
- [[responsive-design|Responsive Design]] — chuyển quyết định bố cục thành quy tắc thích nghi nội dung.
- [[web-accessibility|Web Accessibility]] — bổ sung tiêu chí tiếp cận và kiểm trên implementation.
- [[product-engineering-beyond-system-design|product-engineering-beyond-system-design]] — đặt thiết kế trong chất lượng sản phẩm và vận hành.
- [[MOC-UIUX|MOC: UI/UX]] — bản đồ nguồn, quy tắc và ứng dụng.

## Nguồn

Đối chiếu ngày 2026-09-13; reviewed là đối chiếu tài liệu, không phải kết quả kiểm thử sản phẩm.

- [Penpot — Inspect](https://help.penpot.app/user-guide/dev-tools/)
- [W3C — WCAG 2.2](https://www.w3.org/TR/WCAG22/)
