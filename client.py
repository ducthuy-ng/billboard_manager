import logging
import os
import socket
import ssl
import subprocess

# Server settings
SERVER_ADDR = ("localhost", 8080)
VIDEO_PATH = "./video/received.mp4"


# Connect and receive video
def receive_video():
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile="./certs/ca.cert.pem")
    ssl_context.load_cert_chain("./certs/raspi001.cert.pem", "./certs/raspi001.key.pem")

    with socket.create_connection(SERVER_ADDR) as sock:
        with ssl_context.wrap_socket(sock, server_hostname=SERVER_ADDR[0]) as ssl_sock:
            logging.info("Connected to server, receiving video...")

            total_received = 0
            with open(VIDEO_PATH, "wb") as f:
                while True:
                    chunk = ssl_sock.recv(4096)
                    if not chunk:
                        break
                    f.write(chunk)
                    total_received += len(chunk)

                f.flush()  # Ensure all data is written to disk

            logging.info(f"Video received successfully: {VIDEO_PATH} (Size: {total_received} bytes)")

    logging.info("Connection closed.")


# Play video in loop using VLC
def play_video():
    if not os.path.exists(VIDEO_PATH):
        logging.error("No video file found to play.")
        return

    logging.info("Playing video on loop using VLC...")
    subprocess.Popen(["ffplay", "--loop", VIDEO_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    receive_video()
    play_video()


if __name__ == "__main__":
    main()
