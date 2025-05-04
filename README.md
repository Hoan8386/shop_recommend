# Shop Recommend - Hướng dẫn cài đặt

Đây là hướng dẫn để cài đặt và chạy ứng dụng Shop Recommend.

## Yêu cầu hệ thống
- Python 3.8 hoặc cao hơn
- SQL Server hoặc SQLite (tùy thuộc vào cấu hình)

## Các bước cài đặt

### 1. Cài đặt các thư viện cần thiết

```bash
pip install -r requirements.txt
```

### 2. Cấu hình cơ sở dữ liệu

Đảm bảo cấu hình kết nối cơ sở dữ liệu trong file `db_connection.py` đã chính xác với môi trường của bạn.

### 3. Khởi chạy server

```bash
python api.py
```

Server sẽ chạy mặc định tại địa chỉ http://127.0.0.1:5000/

### 4. Mở ứng dụng web

Mở file `shop.html` hoặc `index.html` trong trình duyệt web để sử dụng ứng dụng.

## Cấu trúc dự án

- `api.py`: API Flask chính của ứng dụng
- `db_connection.py`: Module kết nối với cơ sở dữ liệu
- `shop.js`: Mã JavaScript cho cửa hàng web
- `shop.html`: Giao diện cửa hàng
- `index.html`: Trang chính với dashboard phân tích

## Các tính năng chính

1. Hiển thị sản phẩm và tìm kiếm
2. Hệ thống đăng nhập/đăng ký
3. Quản lý giỏ hàng và đơn hàng
4. Gợi ý sản phẩm cá nhân hóa "For You"
5. Các gợi ý sản phẩm mua kèm dựa trên thuật toán Apriori và chỉ số Lift
6. Dashboard phân tích dữ liệu bán hàng