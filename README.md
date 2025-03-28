# Công nghệ sử dụng

Sử dụng websocket để duy trì và quản lý kết nối dễ hơn. Các thao `send()` và `recv()` tương tự. Có thể tham khảo document tại:
https://websockets.readthedocs.io/en/stable/

# Hướng dẫn lập trình

## Cách setup môi trường dev

1. Cài uv. Đây là 1 trình giúp quản lý thư viện của Python khá tiện lợi và hữu ích.
   Xem cách tải tại đây: https://docs.astral.sh/uv/getting-started/installation/
2. Clone repo này về.

```shell
git clone https://github.com/ducthuy-ng/billboard_manager
cd billboard_manager
```

3. Chạy câu lệnh cài đặt tất cả thư viện cần thiết

```shell
uv sync
```

uv sẽ tạo thư mục `.venv`, tương tự như Python Virtual Environment (môi trường ảo).

## Tạo file certificate
Nếu dùng OS Windows, cài MSYS2. Xem cách tải tại đây: https://www.msys2.org/#installation


```shell
cd billboard_manager

# Tạo file certificate
make

# Xóa file certificate
make clean
```

## Chạỵ code

Có 3 file code: `app.py` sẽ làm web server, `server.py` sẽ làm file sync server, và `client.py` sẽ làm file client.
Muốn chạy file nào, thực hiện

```shell
# Chạy file sync server
uv run app.py

# Chạy file sync server
uv run server.py

# Chạy file client
uv run client.py
```