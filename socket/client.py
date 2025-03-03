import ssl
import socket


def main():
    server_addr = ("localhost", 8080)
    # ssl_context = ssl.create_default_context(cafile="./certs/ca.cert.pem")
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.load_verify_locations("./certs/raspi001.cert.pem")

    with socket.create_connection(server_addr) as sock:
        with ssl_context.wrap_socket(
            sock, server_hostname=server_addr[0]
        ) as ssl_socket:
            print(ssl_socket.read())
            ssl_socket.close()


if __name__ == "__main__":
    main()
