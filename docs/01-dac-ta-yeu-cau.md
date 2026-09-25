# 1. Đặc tả yêu cầu – Hệ thống đặt vé xem phim

## 1.1 Mục tiêu

Hệ thống quản lý một chuỗi rạp chiếu phim gồm các phần: danh mục phim, phòng chiếu và sơ đồ ghế, lịch chiếu, giá vé, đặt vé (online và tại quầy), thanh toán, vé điện tử QR, hoá đơn và báo cáo doanh thu.

Yêu cầu cốt lõi: **mỗi ghế của một suất chiếu chỉ bán được cho đúng một người**, kể cả khi hàng nghìn người cùng đặt lúc mở bán.

## 1.2 Tác nhân

| Tác nhân | Mô tả | Phạm vi dữ liệu |
|---|---|---|
| Khách vãng lai | Chưa đăng nhập: xem phim, lịch chiếu, sơ đồ ghế | Dữ liệu công khai |
| Khách hàng | Đặt vé online, thanh toán, xem/hủy/đổi vé của mình, tích điểm | Đơn và vé của chính mình |
| Nhân viên rạp | Bán vé tại quầy, soát vé QR | Chỉ rạp được gán (`users.cinema_id`) |
| Admin | Quản lý phim, rạp, phòng, ghế, suất chiếu, giá, khuyến mãi, tài khoản; xem báo cáo | Toàn hệ thống |
| Cổng thanh toán (VNPay/MoMo) | Hệ thống ngoài, gọi webhook/IPN báo kết quả giao dịch | |
| Worker (Celery) | Tác nhân hệ thống: nhả ghế hết hạn, gửi email, sinh PDF | |

## 1.3 Yêu cầu chức năng

### F1. Tài khoản và phân quyền
- F1.1 Khách hàng tự đăng ký bằng email và mật khẩu (ít nhất 8 ký tự, gồm cả chữ và số).
- F1.2 Đăng nhập nhận access token (15 phút) và refresh token (7 ngày). Đăng xuất thì thu hồi mọi phiên của tài khoản.
- F1.3 Quên mật khẩu: gửi liên kết qua email, hiệu lực 30 phút, chỉ dùng một lần.
- F1.4 Người dùng tự sửa hồ sơ và đổi mật khẩu; đổi mật khẩu thì đăng xuất mọi thiết bị.
- F1.5 Admin tạo và sửa tài khoản nhân viên hoặc admin, gán rạp cho nhân viên, khoá hoặc mở khoá tài khoản. Admin không thể tự khoá hay tự hạ quyền của mình.
- F1.6 Mọi thao tác ghi của admin và nhân viên đều được ghi vào nhật ký (audit log).

### F2. Danh mục phim
- F2.1 CRUD phim: tên, mô tả, thể loại (nhiều), thời lượng, phân loại độ tuổi (P/K/T13/T16/T18), điểm đánh giá, ngôn ngữ, đạo diễn, ngày khởi chiếu/kết thúc, poster, trailer.
- F2.2 Xoá mềm: phim đã có suất chiếu thì không xoá cứng.
- F2.3 Trang công khai: phim đang chiếu và sắp chiếu, tìm kiếm theo tên, lọc theo thể loại và rạp.

### F3. Rạp, phòng và sơ đồ ghế
- F3.1 CRUD cụm rạp và phòng chiếu. Mỗi phòng có thời gian dọn phòng giữa hai suất (mặc định 15 phút).
- F3.2 Editor sơ đồ ghế: lưới hàng × cột, mỗi ô là ghế thường / VIP / ghế đôi / lối đi. Có thể lưu và áp dụng lại dạng template.
- F3.3 Không được đổi sơ đồ của phòng đang có suất chiếu chưa diễn ra đã bán vé.

### F4. Lịch chiếu và giá vé
- F4.1 CRUD suất chiếu: phim, phòng, giờ bắt đầu, định dạng (2D/3D/IMAX), giá gốc. Giờ kết thúc = giờ bắt đầu + thời lượng phim.
- F4.2 Không cho hai suất trùng phòng: khoảng `[bắt đầu, kết thúc + thời gian dọn phòng)` không được giao nhau.
- F4.3 Bảng giá: giá vé = giá gốc + phụ thu loại ghế + phụ thu khung giờ/ngày (cuối tuần, ngày lễ). Tính bằng Decimal, làm tròn 1.000đ.
- F4.4 Giá được chốt cho từng ghế lúc tạo suất (`showtime_seats.price`).
- F4.5 Huỷ suất chiếu thì tự động hoàn tiền mọi vé đã bán.

### F5. Đặt vé online
- F5.1 Khách chọn suất và xem sơ đồ ghế với trạng thái trống / đang giữ / đã bán, cập nhật realtime.
- F5.2 Chọn tối đa 8 ghế mỗi đơn. Ghế được **giữ 10 phút**; hết hạn thì tự nhả.
- F5.3 Có thể thêm combo bắp nước và áp mã giảm giá.
- F5.4 Thanh toán qua cổng (VNPay sandbox / mock). Thanh toán thành công thì đơn được xác nhận, ghế chuyển sang đã bán, hệ thống sinh vé QR và hoá đơn, rồi gửi email kèm PDF.

### F6. Vé, check-in, hoàn và đổi vé
- F6.1 Mỗi ghế đã bán là một vé với mã QR không đoán được, không làm giả được (token ngẫu nhiên + chữ ký HMAC).
- F6.2 Nhân viên quét QR để check-in. Mỗi vé chỉ check-in được một lần, đúng rạp, trong khoảng từ 30 phút trước đến 15 phút sau giờ chiếu.
- F6.3 Huỷ vé: hoàn 100% nếu còn ≥ 24 giờ trước giờ chiếu, hoàn 70% nếu còn 2–24 giờ, không hoàn nếu < 2 giờ.
- F6.4 Đổi vé sang suất khác của cùng phim: khi còn ≥ 2 giờ trước giờ chiếu, tối đa 1 lần; khách trả thêm phần chênh lệch nếu vé mới đắt hơn.

### F7. Bán vé tại quầy (POS)
- F7.1 Nhân viên chọn suất tại rạp mình, chọn ghế (dùng chung cơ chế giữ ghế), thu tiền mặt, in vé.
- F7.2 Có thể gắn đơn với tài khoản khách để tích điểm.

### F8. Báo cáo
- F8.1 Doanh thu theo phim / suất chiếu / rạp / ngày = tổng thanh toán thành công trừ tổng tiền đã hoàn.
- F8.2 Tỉ lệ lấp đầy theo suất = số ghế đã bán / tổng số ghế.
- F8.3 Dashboard biểu đồ; xuất PDF và CSV.

## 1.4 Quy tắc nghiệp vụ

| Mã | Quy tắc |
|---|---|
| BR1 | Một ghế của một suất chiếu tại mọi thời điểm chỉ ở một trạng thái: `available`, `held`, `sold`, `blocked` |
| BR2 | Ghế `held` quá `held_until` được coi là trống, kể cả khi job dọn dẹp chưa chạy |
| BR3 | Chỉ xác nhận thanh toán khi ghế vẫn đang được giữ cho đúng đơn đó; nếu không, hệ thống tự hoàn tiền |
| BR4 | Không bán vé cho suất đã bắt đầu hoặc đã huỷ |
| BR5 | Nhân viên chỉ thao tác trên dữ liệu thuộc rạp của mình |
| BR6 | Sửa dữ liệu dùng khoá lạc quan `row_version`; nếu phiên bản đã cũ thì API trả 409 |
| BR7 | Tiền tệ là VND, lưu dạng `NUMERIC(12,2)`, không dùng số thực |

## 1.5 Yêu cầu phi chức năng

| Mã | Yêu cầu | Cách đạt |
|---|---|---|
| NFR1 | Không bán trùng ghế khi đặt đồng thời | UPDATE có điều kiện trên `showtime_seats` + UNIQUE; kiểm chứng bằng test 50 luồng và k6 |
| NFR2 | Chịu tải khi mở bán suất hot: p95 < 500 ms với 200 người dùng ảo | k6 (task 8.2), index, cache Redis |
| NFR3 | Rate limit API đặt vé: 10 lần/phút/người; đăng nhập: 5 lần/phút/IP | Redis, trả 429 + `Retry-After` |
| NFR4 | Bảo mật | bcrypt, JWT ngắn hạn, RBAC, CORS whitelist, secret lấy từ biến môi trường, audit log |
| NFR5 | In vé và hoá đơn PDF | ReportLab trong worker |
| NFR6 | Triển khai một lệnh | Docker Compose: api, worker, db, redis, mailhog, web |
| NFR7 | Giao diện tiếng Việt, dùng được trên điện thoại | AngularJS, layout responsive |
