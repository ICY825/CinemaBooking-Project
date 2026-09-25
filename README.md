# Cinema Booking

Hệ thống quản lý rạp chiếu phim: phim, suất chiếu, sơ đồ ghế, đặt vé, vé QR, hoá đơn, báo cáo.
Backend dùng **Python + FastAPI**. Kế hoạch và thiết kế nằm trong [PLAN.md](PLAN.md); tiến độ theo dõi trong `Cinema_Booking_Master_Plan.xlsx`.

## Chạy bằng Docker (Postgres + Redis + MailHog + web)

```bash
cp .env.example .env        # rồi đổi JWT_SECRET
docker compose up -d --build
```

| Địa chỉ | Dùng để |
|---|---|
| http://localhost:8080 | Giao diện web (AngularJS) |
| http://localhost:8000/docs | Swagger: thử trực tiếp từng API (bấm **Authorize**, dán `access_token`) |
| http://localhost:8025 | MailHog: xem email đặt lại mật khẩu |

Tài khoản demo (tự seed khi khởi động), mật khẩu `Cinema@123`:
`admin@cinema.example.com` · `staff@cinema.example.com` · `customer@cinema.example.com`.
Trang đăng nhập có sẵn nút điền nhanh các tài khoản này.

Xoá sạch dữ liệu và seed lại: `docker compose down -v && docker compose up -d --build`.

## Chạy local (SQLite, không cần Docker)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

## Test

```bash
cd backend
python -m pytest -q
```

## Migration

Mỗi lần sửa model trong `backend/app/models/`, tạo migration mới:

```bash
alembic revision --autogenerate -m "mo ta thay doi"
alembic upgrade head
```

## Tài liệu

- [PLAN.md](PLAN.md): kế hoạch, thiết kế kỹ thuật, lịch 9 tuần
- [docs/01-dac-ta-yeu-cau.md](docs/01-dac-ta-yeu-cau.md): đặc tả yêu cầu, quy tắc nghiệp vụ, NFR
- [docs/02-use-case.md](docs/02-use-case.md): sơ đồ và đặc tả use case
- [docs/03-erd.md](docs/03-erd.md): ERD
- [docs/04-sequence-dat-ve.md](docs/04-sequence-dat-ve.md): sequence diagram luồng đặt vé → thanh toán → check-in

Sơ đồ viết bằng Mermaid: xem được trên GitHub/GitLab, hoặc trong VS Code với extension *Markdown Preview Mermaid Support*.

## Trạng thái

| Task | Nội dung | Trạng thái |
|---|---|---|
| 1.1 | Đặc tả, use case, ERD, sequence diagram | Xong |
| 1.2 | Schema + migration 16 bảng | Xong |
| 1.3 | Auth JWT access/refresh, logout thu hồi token, quên/đặt lại mật khẩu, RBAC 3 vai trò, `row_version`, audit log | Xong, 15 test backend |
| 1.4 | UI: đăng nhập, đăng ký, quên/đặt lại mật khẩu, hồ sơ, đổi mật khẩu, quản lý tài khoản, layout 3 vai trò | Xong, E2E 18 bước |
