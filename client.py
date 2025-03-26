import socket
import ssl
import hashlib
import os
import pickle
import shutil
import subprocess
import time
import logging

LOG_FOLDER = "logs/"
os.makedirs(LOG_FOLDER, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/client.log"),
        logging.StreamHandler()
    ]
)

SERVER_HOST = "localhost"
SERVER_PORT = 8443
VIDEO_FOLDER = "client_videos/"
TEMP_FOLDER = "client_videos_temp/"
MAX_RETRIES = 3
MAX_BUFFER = 4096
DELIMITER = b"\n\nEND\n\n"
PLAYLIST_FILE = "playlist.m3u"

os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

def delete_folder_contents(folder_path):
    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
        logging.info(f"All contents of '{folder_path}' have been deleted.")
    else:
        logging.warning(f"The folder '{folder_path}' does not exist.")

def compute_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(MAX_BUFFER):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_video_hash():
    video_hash = []
    try:
        with open(PLAYLIST_FILE, 'r') as file:
            for line in file:
                line = line.strip()
                if not os.path.isfile(line):
                    continue
                video_hash.append(compute_file_hash(line))
    except FileNotFoundError:
        logging.warning("Playlist file not found.")
        return ()
    return tuple(video_hash)

def receive_server_order(conn):
    buffer = b""
    while DELIMITER not in buffer:
        chunk = conn.recv(MAX_BUFFER)
        if not chunk:
            raise ConnectionError("Unexpected disconnection while receiving data.")
        buffer += chunk
    response, remaining_data = buffer.split(DELIMITER, 1)
    return response, remaining_data

def receive_missing_files(conn, initial_data):
    index = 0
    missing_files = []
    get_all_data = False

    while not get_all_data:
        file_path = os.path.join(TEMP_FOLDER, f"{index}.mp4")
        with open(file_path, "wb") as f:
            buffer = initial_data if initial_data else b""
            initial_data = None

            while DELIMITER not in buffer:
                chunk = conn.recv(MAX_BUFFER)
                if not chunk:
                    get_all_data = True
                    break
                buffer += chunk

            if not get_all_data:
                data, initial_data = buffer.split(DELIMITER, 1)
                f.write(data)
                new_file_path = os.path.join(VIDEO_FOLDER, f"{compute_file_hash(file_path)}.mp4")
                missing_files.append((file_path, new_file_path))
        index += 1

    return missing_files

def check_have_all_files(new_order_set, missing_files):
    for temp_file_path, _ in missing_files:
        new_order_set.discard(compute_file_hash(temp_file_path))

    for file in os.listdir(VIDEO_FOLDER):
        file_path = os.path.join(VIDEO_FOLDER, file)
        new_order_set.discard(compute_file_hash(file_path))
    return not new_order_set

def save_playlist(video_list):
    with open(PLAYLIST_FILE, "w") as f:
        for video in video_list:
            f.write(f"{os.path.join(VIDEO_FOLDER, video)}.mp4\n")

def is_vlc_running():
    try:
        result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq vlc.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "vlc.exe" in result.stdout.decode("utf-8")
    except FileNotFoundError:
        logging.error("tasklist command not found.")
        return False

def restart_vlc():
    if is_vlc_running():
        try:
            subprocess.run(["taskkill", "/IM", "vlc.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info("VLC process killed.")
        except Exception as e:
            logging.error(f"Error killing VLC process: {e}")
    else:
        logging.info("VLC not running.")

    time.sleep(1)

    try:
        subprocess.Popen(["vlc", "--loop", "--playlist-autostart", "--no-video-title-show", PLAYLIST_FILE], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info("VLC started.")
    except FileNotFoundError:
        logging.error("VLC executable not found. Please install VLC.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

def request_videos():
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.load_cert_chain(certfile="./certs/raspi001.cert.pem", keyfile="./certs/raspi001.key.pem")
    context.load_verify_locations(cafile="./certs/ca.cert.pem")

    with socket.create_connection((SERVER_HOST, SERVER_PORT)) as sock:
        with context.wrap_socket(sock, server_hostname=SERVER_HOST) as conn:
            conn.sendall(pickle.dumps(get_video_hash()) + DELIMITER)
            response, remaining_data = receive_server_order(conn)

            if not response:
                logging.info("Playlist is up to date.")
                return

            new_order = pickle.loads(response)
            logging.info("Downloading missing files...")
            missing_files = receive_missing_files(conn, remaining_data)
            new_order_set = set(new_order)
            if check_have_all_files(new_order_set.copy(), missing_files):
                for file in os.listdir(VIDEO_FOLDER):
                    file_path = os.path.join(VIDEO_FOLDER, file)
                    if compute_file_hash(file_path) not in new_order_set:
                        os.remove(file_path)

                for temp_file_path, new_file_path in missing_files:
                    shutil.move(temp_file_path, new_file_path)
                delete_folder_contents(TEMP_FOLDER)

                logging.info("Updating playlist order.")
                save_playlist(new_order)
                restart_vlc()
            else:
                logging.error("Missing files.")

    logging.info(f"Playing videos in order: {new_order}")

if __name__ == "__main__":
    request_videos()
