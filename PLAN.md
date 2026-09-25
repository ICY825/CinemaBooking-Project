# Kế hoạch triển khai – Cinema Booking (Python + FastAPI)

Tài liệu này chi tiết hoá `Cinema_Booking_Master_Plan.xlsx` thành thiết kế kỹ thuật và việc cần làm theo tuần.
Tiến độ (trạng thái, % hoàn thành) vẫn cập nhật trong file Excel; tài liệu này trả lời câu hỏi *làm thế nào*.

- Thời gian: 21/09/2026 – 22/11/2026 (~9 tuần, 3 sprint)
- Mốc: **M1 18/10** đặt vé + giữ ghế chạy được · **M2 08/11** thanh toán + quầy + báo cáo · **M3 20/11** demo & bàn giao
- Vai trò: Khách hàng · Nhân viên rạp (bán vé quầy, soát vé) · Admin

---

## 1. Đối chiếu yêu cầu đề tài với master plan

| # | Yêu cầu đề tài | Task trong master plan | Mốc |
|---|---|---|---|
| 1 | Danh mục phim (tên, thể loại, thời lượng, rating) | 2.1, 2.3 | M1 |
| 2 | Lịch chiếu, sơ đồ ghế, định giá theo giờ/ghế | 2.2, 3.1, 3.2, 3.3 | M1 |
| 3 | Đặt vé online, chọn ghế, hold ghế tạm thời | 4.1, 4.2, 4.3 | M1 |
| 4 | Check-in vé QR, hoàn/đổi vé theo chính sách | 5.2, 5.3, 6.2 | M2 |
| 5 | Báo cáo doanh thu theo phim, suất chiếu | 7.1, 7.3 | M2 |
| 6 | Chống đặt trùng ghế, xử lý đồng thời cao | 4.2, 4.4, 8.2 | M1 / M3 |
| NFR | Lock ghế · in vé PDF · rate-limit API đặt vé | 4.2 · 5.2 · 4.2 + 8.1 | |
| Bàn giao | Flow đặt vé → check-in · template sơ đồ ghế · dashboard doanh thu phim | 1.1 + 9.3 · 2.2 · 7.1 | M3 |

**Những điểm master plan còn thiếu, đề xuất bổ sung:**
- **Đổi vé**: task 5.3 mới ghi "hủy vé/hoàn tiền". Cần thêm đổi vé (xem mục 5.4).
- **Hoá đơn (invoices)**: có trong danh sách dữ liệu của đề tài nhưng chưa có task nào. Gộp vào 5.2 (sinh hoá đơn cùng lúc với vé).
- **Rate-limit API đặt vé**: hiện chỉ nằm trong bước rà soát 8.1. Nên làm ngay ở 4.2, vì đây là yêu cầu bắt buộc.

---

## 2. Công nghệ

Đề tài gợi ý .NET 8; nhóm chọn Python. Bảng quy đổi:

| Gợi ý của đề tài | Lựa chọn | Ghi chú |
|---|---|---|
| ASP.NET Core | **FastAPI** (Python 3.11), Pydantic v2 | Tự sinh OpenAPI/Swagger tại `/docs` |
| EF Core migration | **SQLAlchemy 2.0 + Alembic** | |
| SQL Server / PostgreSQL | **PostgreSQL 16** | Test tự động chạy trên SQLite in-memory |
| Cache | **Redis 7** | Pub/sub trạng thái ghế, rate limit, cache dashboard |
| Job nền | **Celery + Redis** (worker + beat) | Nhả ghế hết hạn, gửi email, render PDF |
| QuestPDF | **ReportLab** + `qrcode` | Vé, hoá đơn, báo cáo |
| HTML/CSS/JS (AngularJS) | **AngularJS 1.8** (file local trong `frontend/vendor/`) + nginx | Tận dụng giao diện sơ đồ ghế trong `index.html` |
| Mail | **MailHog** | Xem mail tại http://localhost:8025 |
| Test | pytest + httpx `TestClient`, **k6** (load), Playwright (E2E) | |
| Triển khai | **Docker Compose**: api, worker, beat, db, redis, mailhog, web | |

---

## 3. Kiến trúc & thư mục

```
CinemaBooking/
├─ docker-compose.yml
├─ .env.example
├─ backend/
│  ├─ app/
│  │  ├─ main.py              # tạo FastAPI app, CORS, router
│  │  ├─ core/                # config, security (JWT, bcrypt), deps (auth, RBAC)
│  │  ├─ db/                  # Base, session, mixin (timestamp, row_version, soft delete)
│  │  ├─ models/              # ORM: user, cinema, movie, showtime, booking, audit
│  │  ├─ schemas/             # Pydantic request/response
│  │  ├─ api/v1/              # router theo module
│  │  ├─ services/            # nghiệp vụ: audit, mailer, pricing, seat_hold, payment...
│  │  ├─ workers/             # Celery tasks (Sprint 1 tuần 3 trở đi)
│  │  └─ seed.py
│  ├─ alembic/                # migration
│  └─ tests/
├─ frontend/                  # AngularJS SPA (public / staff / admin)
└─ loadtest/                  # kịch bản k6
```

Nguyên tắc: router chỉ nhận/trả dữ liệu và kiểm quyền; nghiệp vụ nằm trong `services/`, để dùng lại được cho API online, POS và Celery.

---

## 4. Mô hình dữ liệu

| Bảng | Cột chính | Ràng buộc quan trọng |
|---|---|---|
| `users` | email, password_hash, full_name, role (customer/staff/admin), cinema_id (phạm vi của nhân viên), token_version, loyalty_points | email unique |
| `cinemas` | name, city, address | xoá mềm |
| `auditoriums` | cinema_id, name, cleaning_minutes | unique (cinema_id, name) |
| `seats` | auditorium_id, row_label, col_number, seat_type (standard/vip/couple), is_active | unique (auditorium_id, row_label, col_number) |
| `genres`, `movie_genres` | | |
| `movies` | title, duration_minutes, age_rating (P/K/T13/T16/T18), rating (điểm), release_date, poster_url, trailer_url | xoá mềm |
| `showtimes` | movie_id, auditorium_id, starts_at, ends_at, format (2D/3D/IMAX), base_price, status | chặn trùng phòng (kiểm tra ở service) |
| `price_rules` | seat_type, day_type, time_from/time_to, format, surcharge, priority | |
| `holidays` | date, name | |
| `showtime_seats` | showtime_id, seat_id, status (available/held/sold/blocked), reservation_id, held_until, price | **unique (showtime_id, seat_id)** |
| `reservations` | code, user_id, showtime_id, channel (online/counter), status, expires_at, subtotal, discount, total | code unique |
| `tickets` | reservation_id, showtime_seat_id, code (QR), price, status (valid/used/cancelled/refunded), checked_in_at/by | code unique |
| `invoices` | reservation_id, number, subtotal, discount, vat, total, pdf_path | number unique |
| `payments` | reservation_id, provider, amount, status, provider_txn_id, idempotency_key | idempotency_key unique |
| `audit_logs` | actor_id, action, entity_type, entity_id, before, after, ip | |

Mọi bảng có `created_at`/`updated_at`. Các bảng hay bị sửa đồng thời (users, showtimes, showtime_seats, reservations, payments) có thêm `row_version` để khoá lạc quan (optimistic lock): client gửi kèm `row_version`, và nếu bản ghi đã bị người khác sửa trước thì API trả 409.

---

## 5. Thiết kế các phần khó

### 5.1 Giữ ghế và chống đặt trùng (yêu cầu 3, 6)

- Khi tạo suất chiếu, hệ thống sinh sẵn `showtime_seats` (mỗi ghế một dòng) và chốt giá vào cột `price`.
- **Giữ ghế là một câu UPDATE có điều kiện, chạy trong một transaction:**
  ```sql
  UPDATE showtime_seats
     SET status='held', reservation_id=:rid, held_until=now()+interval '10 min', row_version=row_version+1
   WHERE showtime_id=:sid AND seat_id = ANY(:seat_ids)
     AND (status='available' OR (status='held' AND held_until < now()));
  ```
  Nếu số dòng bị ảnh hưởng nhỏ hơn số ghế yêu cầu thì rollback toàn bộ và trả `409 SEAT_TAKEN`. Postgres khoá theo dòng nên hai request tranh cùng một ghế thì chỉ một request thắng.
- Database là nơi quyết định cuối cùng. Redis chỉ làm các việc phụ: (a) có thể thêm `SET NX` để từ chối sớm khi quá tải, (b) pub/sub đẩy trạng thái ghế lên WebSocket, (c) rate limit. Vì vậy Redis có sập thì vẫn không bán trùng ghế.
- Khi thanh toán xong: `UPDATE ... SET status='sold' WHERE reservation_id=:rid AND held_until >= now()`. Nếu lúc đó ghế đã hết hạn giữ, đơn chuyển sang trạng thái hoàn tiền tự động.
- Celery beat chạy mỗi 30 giây: nhả các ghế `held` đã quá hạn và chuyển đơn sang `expired`. Job này có chạy chậm cũng không sao, vì câu UPDATE ở trên đã coi ghế hết hạn là ghế trống.
- Test 4.4: 50 luồng cùng giữ một ghế thì đúng 1 luồng thành công, 49 luồng nhận 409. Chạy trên Postgres thật (docker), không chạy trên SQLite.

### 5.2 Định giá (yêu cầu 2)

`giá = base_price(suất, theo định dạng) + phụ thu loại ghế + phụ thu khung giờ/ngày (cuối tuần, ngày lễ)`

- Luôn tính bằng `Decimal` và làm tròn đến 1.000đ.
- Giá được chốt vào `showtime_seats.price` lúc tạo suất, nên sửa bảng giá sau đó không ảnh hưởng tới vé đã bán.
- Khi có nhiều quy tắc cùng khớp thì áp dụng theo `priority`.

### 5.3 Vé QR và check-in (yêu cầu 4)

- `tickets.code` = `secrets.token_urlsafe(16)`. Nội dung QR = `CB1.<code>.<HMAC-SHA256 rút gọn>`, nên không thể đoán mã hoặc tự tạo vé giả.
- Check-in: `UPDATE tickets SET status='used', checked_in_at=now(), checked_in_by=:staff WHERE code=:c AND status='valid'`. Câu lệnh atomic nên một vé không thể dùng lại lần hai.
- Trước khi check-in, kiểm tra thêm: vé đúng rạp của nhân viên, và thời điểm quét nằm trong khoảng từ 30 phút trước đến 15 phút sau giờ chiếu.
- Vé PDF gồm thông tin suất chiếu và mã QR. Worker render PDF, lưu vào thư mục private, người dùng tải qua endpoint có xác thực.

### 5.4 Hoàn / đổi vé (yêu cầu 4)

Chính sách được lưu trong cấu hình nên có thể chỉnh:

| Thời điểm so với giờ chiếu | Hủy vé | Đổi vé |
|---|---|---|
| ≥ 24 giờ | Hoàn 100% | Được đổi (cùng phim, tối đa 1 lần) |
| 2 – 24 giờ | Hoàn 70% | Được đổi |
| < 2 giờ hoặc đã check-in | Không hoàn | Không đổi |

Đổi vé gồm 3 bước trong một transaction: giữ ghế ở suất mới, hủy vé cũ, rồi thu thêm tiền chênh lệch (nếu vé mới rẻ hơn thì không hoàn phần chênh lệch).

### 5.5 Rate limit (NFR)

Dùng Redis, đếm theo cửa sổ thời gian cố định, khoá theo `user_id` (hoặc IP nếu chưa đăng nhập):
- `POST /reservations` (giữ ghế): 10 lần/phút
- `POST /auth/login`: 5 lần/phút

Vượt ngưỡng thì trả `429` kèm header `Retry-After`.

### 5.6 Thanh toán

- Dùng VNPay sandbox, cộng thêm một provider `mock` để demo mà không cần mạng.
- Luồng trạng thái: `pending → succeeded | failed`, sau đó có thể `→ refunded`.
- Webhook/IPN phải kiểm tra checksum và xử lý idempotent theo `provider_txn_id`: nhận trùng webhook không làm đổi kết quả.
- Việc gửi email và tạo PDF được ghi vào outbox, rồi worker xử lý.

### 5.7 Báo cáo (yêu cầu 5)

- Doanh thu = tổng thanh toán thành công trừ tổng tiền đã hoàn, nhóm theo phim / suất chiếu / rạp / ngày.
- Tỉ lệ lấp đầy = số ghế đã bán / tổng số ghế của suất.
- Kết quả cache trong Redis 5 phút, key gồm phạm vi (rạp, khoảng ngày).
- Xuất được PDF và CSV.

---

## 6. API chính (`/api/v1`)

| Module | Endpoint | Quyền |
|---|---|---|
| Auth | `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/forgot-password`, `/auth/reset-password` | public |
| Users | `GET/PATCH /users/me`, `POST /users/me/change-password` | đã đăng nhập |
| | `GET/POST /users`, `PATCH /users/{id}` | admin |
| Movies | `GET /movies`, `GET /movies/{id}` | public |
| | `POST/PATCH/DELETE /movies/{id}` | admin |
| Cinemas | `GET /cinemas`, `/auditoriums/{id}/seat-map` | public |
| | CRUD cinemas/auditoriums, `PUT /auditoriums/{id}/seats` (lưu template sơ đồ ghế) | admin |
| Showtimes | `GET /showtimes?movie&cinema&date&format`, `GET /showtimes/{id}/seats` | public |
| | CRUD showtimes, price rules | admin |
| Booking | `POST /reservations` (giữ ghế), `POST /reservations/{id}/checkout`, `POST /reservations/{id}/cancel`, `POST /tickets/{id}/exchange` | khách / nhân viên |
| Payment | `POST /payments/{provider}/ipn` | cổng thanh toán |
| Staff | `POST /pos/sales`, `POST /checkin` | nhân viên |
| Reports | `GET /reports/revenue?group_by=movie\|showtime\|cinema`, `/reports/occupancy`, `.pdf/.csv` | admin |
| Realtime | `WS /ws/showtimes/{id}` | public |

---

## 7. Lịch làm việc theo tuần

| Tuần | Ngày | Task | Kết quả cần có |
|---|---|---|---|
| 1 | 21–27/09 | 1.1–1.4 | Đặc tả, use case, ERD, sequence đặt vé; schema + Alembic; auth JWT/refresh/reset, RBAC, row_version, audit; UI đăng nhập/hồ sơ, layout 3 vai trò |
| 2 | 28/09–04/10 | 2.1–2.4 | CRUD phim, rạp/phòng, **editor sơ đồ ghế**; trang public; seed ≥ 2.000 bản ghi |
| 3 | 05–11/10 | 3.1–3.5 | CRUD suất chiếu (chặn trùng phòng, cộng thời gian dọn phòng), bảng giá, trang chọn suất; Celery/Redis; thử nghiệm PDF/QR |
| 4 | 12–18/10 | 4.1–4.4 | Sơ đồ ghế realtime, giữ ghế 10 phút, rate limit, đơn + combo + voucher, **test đồng thời** → **M1** |
| 5 | 19–25/10 | 5.1–5.4 | VNPay sandbox/mock, vé QR + PDF + hoá đơn + email, hủy/đổi vé, đối soát |
| 6 | 26/10–01/11 | 6.1–6.4 | POS tại quầy, **check-in QR**, thành viên/điểm, xem audit |
| 7 | 02–08/11 | 7.1–7.3 | **Dashboard doanh thu**, khuyến mãi, xuất nhập CSV/Excel, báo cáo PDF → **M2** |
| 8 | 09–11/11 | 8.1–8.3 | Rà soát bảo mật, load test k6, E2E |
| 9 | 12–20/11 | 9.1–9.3 | CI/CD, deploy demo, tài liệu + Postman, video demo → **M3** |

**Trạng thái hiện tại (25/09):** tuần 1 đã xong (1.1–1.4). Xem `README.md` để chạy, `docs/` cho tài liệu 1.1.

---

## 8. Definition of Done cho mỗi task

- API có schema Pydantic, kiểm quyền đúng vai trò và có test pytest (cả trường hợp thành công lẫn lỗi 400/401/403/409).
- Thay đổi schema phải đi kèm migration Alembic; không sửa DB bằng tay.
- Mọi thao tác ghi của admin/nhân viên đều ghi `audit_logs`.
- Có UI tương ứng, và hiển thị lỗi từ API bằng tiếng Việt.
- Đánh dấu hoàn thành trong file Excel master plan.

## 9. Rủi ro và cách giảm thiểu

| Rủi ro | Cách giảm thiểu |
|---|---|
| Chỉ một người làm (mọi task giao "Đạt"), dễ trễ | Giữ phạm vi M1 tối thiểu; combo/voucher (4.3) và thành viên (6.3) có thể lùi nếu chậm |
| Sandbox cổng thanh toán không ổn định khi demo | Provider `mock` bật bằng biến môi trường |
| Test đồng thời trên SQLite không phản ánh đúng thực tế | Test 4.4 và k6 bắt buộc chạy trên Postgres trong docker |
| Lệch múi giờ giữa server và suất chiếu | Lưu UTC; hiển thị theo `Asia/Ho_Chi_Minh` |
