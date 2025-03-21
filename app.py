from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digital_signage.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
    """Calculate SHA-256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


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
    # Ensure description max length is 10
    description = request.form.get('description', '')[:10]

    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))

    # Temporarily save the file to calculate the hash
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(temp_path)
    file_hash = calculate_hash(temp_path)

    # Check if hash already exists
    # if Video.query.filter_by(hash=file_hash).first():
    #     os.remove(temp_path)  # Remove temp file
    #     flash('Video already exists!', 'info')
    #     return redirect(url_for('index'))

    new_video = Video(filename=file.filename, hash=file_hash,
                      description=description)
    db.session.add(new_video)
    db.session.commit()

    new_filename = f"{new_video.id}.mp4"
    new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    os.rename(temp_path, new_filepath)

    # new_video.filename = new_filename
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
    data = request.json.get('order')
    if not data:
        return jsonify({'message': 'Invalid order data'}), 400

    for index, video_id in enumerate(data):
        video = db.session.get(Video, video_id)
        if video:
            video.order_index = index

    db.session.commit()
    return jsonify({'message': 'Order updated successfully'})


if __name__ == '__main__':
    app.run(debug=True)
