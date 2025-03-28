import os
import shutil
import subprocess
import zipfile

VIDEO_FOLDER = os.getcwd()

def compress_with_ffmpeg(input_file, output_file):
    command = [
        'ffmpeg', '-y', '-i', input_file, '-vcodec', 'libx264', '-crf', '28', output_file
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        print(f"Error compressing video with ffmpeg: {input_file}")

def compress_with_zip(input_file, output_file):
    try:
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(input_file, os.path.basename(input_file))
    except Exception as e:
        print(f"Error compressing video with zipfile: {input_file} - {e}")

def compress_with_shutil(input_file, output_file):
    try:
        shutil.make_archive(output_file, 'gztar', os.path.dirname(input_file), os.path.basename(input_file))
    except Exception as e:
        print(f"Error compressing video with shutil: {input_file} - {e}")

def compress_video(input_file):
    file_name, file_extension = os.path.splitext(input_file)
    
    ffmpeg_output = f"{file_name}_ffmpeg{file_extension}"
    compress_with_ffmpeg(input_file, ffmpeg_output)
    
    zip_output = f"{file_name}_zipfile.zip"
    compress_with_zip(input_file, zip_output)

    shutil_output = f"{file_name}_shutil.tar.gz"
    compress_with_shutil(input_file, shutil_output)

def process_all_videos_in_folder(folder_path):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        
        if os.path.isfile(file_path) and file_name.lower().endswith('.mp4'):
            print(f"Processing video: {file_name}")
            compress_video(file_path)
        else:
            print(f"Skipping non-video file: {file_name}")

if __name__ == '__main__':
    process_all_videos_in_folder(VIDEO_FOLDER)
