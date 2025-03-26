from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib
import shutil
import subprocess
import re
import unicodedata
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digital_signage.db'
app.config['UPLOAD_FOLDER'] = 'server_videos'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

LOG_FOLDER = "logs"
LOG_FILE_PATH = os.path.join(LOG_FOLDER, "server.log")

os.makedirs(LOG_FOLDER, exist_ok=True)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    hash = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(10), nullable=True)
    order_index = db.Column(db.Integer, nullable=True)
    date_added = db.Column(db.DateTime, default=db.func.current_timestamp())
    deleted = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

def calculate_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()

def is_valid_mp4(file_path):
    """Check if the file is a valid MP4 using ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
             'format=format_name', '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip().lower() == 'mov,mp4,m4a,3gp,3g2,mj2'
    except subprocess.CalledProcessError:
        return False

@app.route('/')
def index():
    videos = Video.query.filter_by(deleted=False).order_by(Video.order_index.is_(
        None), Video.order_index, Video.date_added, Video.filename).all()
    return render_template('index.html', videos=videos)

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))

    file = request.files['file']
    description = request.form.get('description', '')

    description = unicodedata.normalize('NFC', description)
    description = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF]', '', description)[:10]

    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))

    original_filename = unicodedata.normalize('NFC', file.filename)
    filename = secure_filename(original_filename)

    if not filename:
        flash('Invalid filename', 'error')
        return redirect(url_for('index'))

    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(temp_path)

    if not is_valid_mp4(temp_path):
        os.remove(temp_path)
        flash('Invalid MP4 file!', 'error')
        return redirect(url_for('index'))

    file_hash = calculate_hash(temp_path)

    if Video.query.filter_by(hash=file_hash, deleted=False).first():
        os.remove(temp_path)
        flash('Video already exists!', 'info')
        return redirect(url_for('index'))

    new_video = Video(filename=filename, hash=file_hash, description=description)
    db.session.add(new_video)
    db.session.commit()

    new_filename = f"{file_hash}.mp4"
    new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    shutil.move(temp_path, new_filepath)

    new_video.filename = new_filename
    db.session.commit()

    flash('Video uploaded successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/delete_video/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    video = db.session.get(Video, video_id)
    if video:
        video.deleted = True
        db.session.commit()
        return jsonify({'message': 'Video deleted successfully'}), 200
    return jsonify({'message': 'Video not found'}), 404

@app.route('/save_order', methods=['POST'])
def save_order():
    if not request.is_json:
        return jsonify({'message': 'Invalid request format'}), 400

    data = request.json.get('order', [])
    if not isinstance(data, list) or not all(isinstance(i, int) for i in data):
        return jsonify({'message': 'Invalid order data'}), 400

    for index, video_id in enumerate(data):
        video = db.session.get(Video, video_id)
        if video:
            video.order_index = index

    db.session.commit()
    return jsonify({'message': 'Order updated successfully'})

@app.route('/logs')
def view_logs():
    logs = []
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "r") as file:
            logs = file.readlines()
    
    logs = logs[::-1]
    return render_template("logs.html", logs=logs)

if __name__ == '__main__':
    app.run(debug=True)
