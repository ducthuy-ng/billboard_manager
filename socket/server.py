import socket
import ssl


def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain("./certs/raspi001.cert.pem", "./certs/raspi001.key.pem")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("0.0.0.0", 8080))
        sock.listen(5)

        with ssl_context.wrap_socket(sock, server_side=True) as ssl_sock:
            conn, addr = ssl_sock.accept()
            written_bytes = conn.write(b"Hello")
            print(written_bytes)
            conn.close()


if __name__ == "__main__":
    main()
