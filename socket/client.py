import ssl
import socket


def main():
    server_addr = ("localhost", 8080)
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile="./certs/ca.cert.pem")
    ssl_context.load_cert_chain("./certs/raspi001.cert.pem", "./certs/raspi001.key.pem")

    with socket.create_connection(server_addr) as sock:
        with ssl_context.wrap_socket(sock, server_hostname=server_addr[0]) as ssl_socket:
            print(ssl_socket.recv(1024))
            ssl_socket.close()


if __name__ == "__main__":
    main()
