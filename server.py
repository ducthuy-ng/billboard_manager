import socket
import ssl
import hashlib
import os
import signal
import sys
import pickle
import sqlite3
import threading
import logging

LOG_FOLDER = "logs/"
os.makedirs(LOG_FOLDER, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

VIDEO_FOLDER = "server_videos/"
DB_PATH = "instance/digital_signage.db"
MAX_BUFFER = 4096
DELIMITER = b"\n\nEND\n\n"

os.makedirs(VIDEO_FOLDER, exist_ok=True)

def get_video_hash():
    """Fetch the hashes of non-deleted videos from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT hash FROM video WHERE deleted = 0 ORDER BY order_index ASC, date_added ASC, filename ASC")
        rows = cursor.fetchall()
        return tuple(row[0] for row in rows)
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return None
    finally:
        conn.close()

def receive_client_order(conn):
    """Receive and parse the client's video order list."""
    buffer = b""
    while DELIMITER not in buffer:
        try:
            chunk = conn.recv(MAX_BUFFER)
            if not chunk:
                logging.warning("Client disconnected unexpectedly during data reception.")
                return None
            buffer += chunk
        except ConnectionResetError:
            logging.warning("Client forcibly closed the connection.")
            return None
        except Exception as e:
            logging.error(f"Error receiving data: {e}")
            return None

    try:
        data, _ = buffer.split(DELIMITER, 1)
        return pickle.loads(data)
    except (pickle.PickleError, ValueError) as e:
        logging.error(f"Error parsing client order: {e}")
        return None

def handle_client(conn, addr):
    """Handle client requests and send missing videos."""
    try:
        logging.info(f"New client connected: {addr}")
        client_order = receive_client_order(conn)
        # if client_order is None:
        #     return

        server_order = get_video_hash()
        if client_order == server_order:
            conn.sendall(DELIMITER)
            logging.info(f"No new videos for client {addr}.")
            return

        conn.sendall(pickle.dumps(server_order) + DELIMITER)
        logging.info(f"Sent video hash list to client {addr}.")

        if sorted(client_order) == sorted(server_order):
            return

        missing_files = [h for h in server_order if h not in client_order]
        for h in missing_files:
            file_path = os.path.join(VIDEO_FOLDER, f"{h}.mp4")
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(MAX_BUFFER):
                        conn.sendall(chunk)
                conn.sendall(DELIMITER)
                logging.info(f"Sent video file {file_path} to client {addr}.")
            except FileNotFoundError:
                logging.warning(f"Missing file {file_path} requested by client {addr}.")
            except Exception as e:
                logging.error(f"Error sending file {file_path} to client {addr}: {e}")

    except Exception as e:
        logging.error(f"Error handling client {addr}: {e}")
    finally:
        conn.close()
        logging.info(f"Connection closed: {addr}")

def signal_handler(sig, frame):
    """Graceful shutdown handler."""
    logging.info("Shutting down server...")
    sys.exit(0)

def start_server():
    """Initialize the server and listen for client connections."""
    signal.signal(signal.SIGINT, signal_handler)

    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="./certs/server.cert.pem", keyfile="./certs/server.key.pem")
    context.load_verify_locations(cafile="./certs/ca.cert.pem")
    context.verify_mode = ssl.CERT_REQUIRED

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", 8443))
    server_socket.listen(5)
    
    logging.info("Server listening on port 8443...")

    while True:
        try:
            conn, addr = server_socket.accept()
            conn = context.wrap_socket(conn, server_side=True)

            client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_thread.start()

        except ssl.SSLError as e:
            logging.error(f"SSL error: {e}")
        except socket.error as e:
            logging.error(f"Socket error: {e}")
        except Exception as e:
            logging.critical(f"Unexpected server error: {e}")

if __name__ == "__main__":
    start_server()
