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

# Chạỵ code

Có 2 file code: `main.py` sẽ làm file server, và `billboard.py` sẽ làm file client.
Muốn chạy file nào, thực hiện

```shell
# Chạy file server
uv run main.py

# Chạy file client
uv run billboard.py
```