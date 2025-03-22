import socket
import ssl


def main():
    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH, cafile="./certs/ca.cert.pem")
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.load_cert_chain("./certs/server.cert.pem", "./certs/server.key.pem")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", 8080))
        sock.listen()

        with ssl_context.wrap_socket(sock, server_side=True) as ssl_sock:
            conn, _ = ssl_sock.accept()
            conn.do_handshake(block=True)

            conn.send(b"Hello")
            conn.close()


if __name__ == "__main__":
    main()
