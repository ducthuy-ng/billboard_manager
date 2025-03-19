import socket
import ssl
import os
import subprocess
import logging
import signal
import shutil

# Global flag to stop the server
running = True

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Server settings
HOST = "0.0.0.0"
PORT = 8080
VIDEO_INPUT = "./video/input.mp4"  # Original video
VIDEO_OUTPUT = "./video/output.mp4"  # Compressed video

def handle_signal(signum, frame):
    global running
    logging.info("Shutting down server...")
    running = False

# Compress video using FFmpeg
def compress_video(input_file, output_file):
    if not os.path.exists(input_file):
        logging.error(f"Video file {input_file} not found.")
        return False

    logging.info(f"Compressing {input_file}...")
    cmd = [
        "ffmpeg", "-y", "-i", input_file, "-c:v", "libx264", "-crf", "23", "-preset", "slow",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", output_file
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        original_size = os.path.getsize(input_file)
        compressed_size = os.path.getsize(output_file)

        if compressed_size >= original_size:
            logging.warning(f"Compressed file {output_file} is larger than original. Copying original instead.")
            shutil.copy2(input_file, output_file)
            # copy_cmd = ["ffmpeg", "-y", "-i", input_file, "-c", "copy", output_file]
            # subprocess.run(copy_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True

        logging.info(f"Compression successful: {output_file} (Size reduced)")
        return True

    except subprocess.CalledProcessError:
        logging.error("FFmpeg compression failed.")
        return False
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return False

# Start server
def start_server():
    global running

    # Set up TLS
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain("./certs/raspi001.cert.pem", "./certs/raspi001.key.pem")

    # Create socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen(5)
        logging.info(f"Server listening on {HOST}:{PORT}")

        with ssl_context.wrap_socket(sock, server_side=True) as ssl_sock:
            while running:
                try:
                    ssl_sock.settimeout(1)  # Allow periodic checks for stopping
                    conn, addr = ssl_sock.accept()
                    logging.info(f"Client connected: {addr}")

                    # Compress video before sending
                    # if compress_video(VIDEO_INPUT, VIDEO_OUTPUT):
                    #     send_video(conn, VIDEO_OUTPUT)
                    send_video(conn, VIDEO_INPUT)

                    conn.close()
                except socket.timeout:
                    continue  # Allows loop to check 'running' flag
                except Exception as e:
                    logging.error(f"Error: {e}")

    logging.info("Server stopped.")

# Send video file in chunks
def send_video(conn, file_path):
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):  # 4KB chunk size
                conn.sendall(chunk)
        logging.info(f"Sent video: {file_path}")
    except Exception as e:
        logging.error(f"Error sending video: {e}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    start_server()
