# 3. ERD

Sơ đồ khớp với các model trong `backend/app/models/` và migration `backend/alembic/versions/*_0001_initial_schema.py`.
Các cột `created_at`, `updated_at` có ở hầu hết bảng nên được lược bớt khỏi sơ đồ.

```mermaid
erDiagram
  cinemas ||--o{ auditoriums : "có"
  cinemas ||--o{ users : "nhân viên thuộc"
  auditoriums ||--o{ seats : "gồm"
  auditoriums ||--o{ showtimes : "chiếu tại"
  movies ||--o{ showtimes : "được chiếu"
  movies }o--o{ genres : "movie_genres"
  showtimes ||--o{ showtime_seats : "tồn kho ghế"
  seats ||--o{ showtime_seats : ""
  showtimes ||--o{ reservations : ""
  users |o--o{ reservations : "đặt"
  reservations |o--o{ showtime_seats : "giữ / mua"
  reservations ||--o{ tickets : ""
  showtime_seats ||--o| tickets : ""
  reservations ||--o| invoices : ""
  reservations ||--o{ payments : ""
  users |o--o{ audit_logs : "thực hiện"

  users {
    int id PK
    string email UK
    string password_hash
    string full_name
    string phone
    string role "customer|staff|admin"
    bool is_active
    int cinema_id FK "chỉ với staff"
    int token_version "thu hồi token"
    int loyalty_points
    int row_version
  }
  cinemas {
    int id PK
    string name UK
    string city
    string address
    datetime deleted_at
  }
  auditoriums {
    int id PK
    int cinema_id FK
    string name "UK(cinema_id,name)"
    int cleaning_minutes
  }
  seats {
    int id PK
    int auditorium_id FK
    string row_label "UK(auditorium,row,col)"
    int col_number
    string seat_type "standard|vip|couple"
    bool is_active
  }
  movies {
    int id PK
    string title
    int duration_minutes
    string age_rating "P|K|T13|T16|T18"
    decimal rating
    date release_date
    string poster_url
    datetime deleted_at
  }
  genres {
    int id PK
    string name UK
  }
  showtimes {
    int id PK
    int movie_id FK
    int auditorium_id FK
    datetime starts_at
    datetime ends_at
    string format "2D|3D|IMAX"
    decimal base_price
    string status
    int row_version
  }
  price_rules {
    int id PK
    string seat_type
    string day_type "weekday|weekend|holiday"
    string format
    time time_from
    time time_to
    decimal surcharge
    int priority
  }
  holidays {
    date day PK
    string name
  }
  showtime_seats {
    int id PK
    int showtime_id FK "UK(showtime_id,seat_id)"
    int seat_id FK
    string status "available|held|sold|blocked"
    int reservation_id FK
    datetime held_until
    decimal price
    int row_version
  }
  reservations {
    int id PK
    string code UK
    int user_id FK
    int created_by_id FK
    int showtime_id FK
    string channel "online|counter"
    string status "pending|confirmed|cancelled|expired|refunded"
    datetime expires_at
    decimal total
    int row_version
  }
  tickets {
    int id PK
    int reservation_id FK
    int showtime_seat_id FK
    string code UK "nội dung QR"
    decimal price
    string status "valid|used|cancelled|refunded"
    datetime checked_in_at
    int checked_in_by_id FK
  }
  invoices {
    int id PK
    int reservation_id FK "UK"
    string number UK
    decimal subtotal
    decimal vat
    decimal total
    string pdf_path
  }
  payments {
    int id PK
    int reservation_id FK
    string provider "vnpay|momo|cash|mock"
    decimal amount
    string status "pending|succeeded|failed|refunded"
    string provider_txn_id UK
    string idempotency_key UK
    json raw_payload
  }
  audit_logs {
    int id PK
    int actor_id FK
    string action
    string entity_type
    string entity_id
    json before
    json after
    string ip
  }
```

## Ghi chú thiết kế

- **`showtime_seats` là trung tâm của việc chống đặt trùng.** Mỗi suất sinh sẵn một dòng cho mỗi ghế. Giữ ghế là câu `UPDATE ... WHERE status='available' OR (status='held' AND held_until < now())`, nên hai người không thể cùng giữ một ghế. Ràng buộc UNIQUE(showtime_id, seat_id) đảm bảo không có hai dòng cho cùng một ghế.
- **Giá được chốt** vào `showtime_seats.price` và `tickets.price`, nên sửa bảng giá sau đó không làm sai doanh thu cũ.
- **`reservations.user_id` có thể null**: dùng cho khách mua tại quầy mà không có tài khoản.
- **`token_version`**: tăng lên thì mọi JWT đã phát cho tài khoản đó (access, refresh, reset) đều mất hiệu lực.
- **`row_version`**: SQLAlchemy tự tăng mỗi lần UPDATE; dùng để phát hiện hai người sửa cùng lúc.
- **Enum lưu dạng VARCHAR** để thêm giá trị mới mà không cần `ALTER TYPE`, và chạy được trên cả SQLite lẫn Postgres.
