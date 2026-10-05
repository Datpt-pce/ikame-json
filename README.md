# ikame-json

Workspace chuyên cho quy trình tạo, kiểm tra và bàn giao Lottie JSON dùng trong ứng dụng.

## Bắt đầu

- Quy ước chung cho agent: [MASTER.MD](MASTER.MD)
- Kho kiến thức: [JSON-Library/README.md](JSON-Library/README.md)
- Khu vực dự án và triển khai: [JSON-Project/README.md](JSON-Project/README.md)
- Theo dõi công việc nhiều phiên: [JSON-Project/specs/MASTER.md](JSON-Project/specs/MASTER.md)

Toolkit dự án cung cấp 79 skills cho Codex và Claude Code, CodeGraph cục bộ và các
policy khảo sát/an toàn. Sau khi clone hoặc đổi môi trường, kiểm tra cài đặt bằng:

```bash
node .agent-toolkit/codegraph.mjs status --json
```

## Phạm vi tri thức hiện có

Snapshot hiện tại bao gồm workflow từ layer thiết kế đến artifact Lottie JSON hoặc
dotLottie, Bodymovin/LottieFiles, tương thích runtime, QA và developer handoff.
Đây là tài liệu làm việc; một file pass schema hoặc preview chưa đủ chứng minh chạy
đúng trên player, renderer và thiết bị đích.

## Bàn giao hiện tại

- **Progress:** toolkit đã bootstrap; bộ 8 tài liệu Lottie JSON đã được snapshot
  trong `JSON-Library/`; `JSON-Project/` đã sẵn sàng cho các triển khai cụ thể.
- **Decisions:** kiến thức tái sử dụng thuộc `JSON-Library/`; dự án và artifact triển
  khai thuộc `JSON-Project/`; commit nguồn được pin để truy vết.
- **Next Steps:** khi có layer/AEP hoặc yêu cầu animation cụ thể, chốt runtime
  contract và acceptance matrix trước khi tạo artifact đầu tiên.
