# JSON-Project

Không gian dành cho các dự án và lần triển khai JSON cụ thể.

Theo dõi outcome và công việc nhiều phiên tại [specs/MASTER.md](specs/MASTER.md).

Mỗi dự án tạo một thư mục riêng:

```text
JSON-Project/
└── <project-slug>/
    ├── README.md
    ├── src/          # JSON nguồn hoặc generator
    ├── assets/       # asset thuộc riêng dự án
    ├── tests/        # validation/regression fixtures
    └── dist/         # artifact bàn giao khi dự án cho phép track
```

`README.md` của từng dự án phải ghi runtime contract, input, acceptance, cách kiểm
chứng và đường dẫn tới kiến thức dùng từ `../../JSON-Library/`. Chỉ tạo các thư mục
con thực sự cần; cây trên là định hướng, không phải scaffold bắt buộc.
