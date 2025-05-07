import os
from flask import Flask, render_template, request, redirect, url_for
import face_recognition
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)

BASE_DIR = 'static/photos'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
loaded_encodings = {}

def load_known_faces(event):
    """Load face encodings from the selected event."""
    if event in loaded_encodings:
        return loaded_encodings[event]

    folder_path = os.path.join(BASE_DIR, event)
    known_faces = []
    if not os.path.exists(folder_path):
        return []

    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        image = face_recognition.load_image_file(filepath)
        encodings = face_recognition.face_encodings(image)
        for encoding in encodings:
            known_faces.append((encoding, filename))

    loaded_encodings[event] = known_faces
    return known_faces

@app.route('/')
def index():
    """Show the event selection page."""
    events = os.listdir(BASE_DIR)
    return render_template('index.html', events=events)

@app.route('/select_event', methods=['POST'])
def select_event():
    """User selects an event."""
    selected_event = request.form.get('event')
    if not selected_event:
        return "No event selected", 400
    return render_template('upload.html', event=selected_event)

@app.route('/upload', methods=['POST'])
def upload():
    """Handle image upload or capture and perform face matching."""
    event = request.form.get('event')
    if not event:
        return "Event not specified", 400

    if 'image' not in request.files and 'image' not in request.form:
        return "No image uploaded", 400

    # Handle image upload
    if 'image' in request.files:
        file = request.files['image']
        if file.filename == '':
            return "No selected file", 400
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
    else:
        # Handle captured image (base64)
        data_url = request.form['image']
        if ',' not in data_url:
            return "Invalid image format", 400
        header, encoded = data_url.split(',', 1)
        image_data = base64.b64decode(encoded)
        img = Image.open(BytesIO(image_data))
        filename = 'captured.jpg'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        img.save(filepath)

    # Perform face recognition
    uploaded_image = face_recognition.load_image_file(filepath)
    uploaded_encodings = face_recognition.face_encodings(uploaded_image)

    if not uploaded_encodings:
        return render_template('upload.html', event=event, message="No face detected.", captured_image=filename)

    uploaded_encoding = uploaded_encodings[0]
    threshold = 0.51  # Face distance threshold
    matches = []
    seen_filenames = set()

    known_faces = load_known_faces(event)
    for known_encoding, known_filename in known_faces:
        if known_filename in seen_filenames:
            continue
        distance = face_recognition.face_distance([known_encoding], uploaded_encoding)[0]
        if distance < threshold:
            matches.append(known_filename)
            seen_filenames.add(known_filename)

    print(f"Matches found: {matches}")  # Debugging

    return render_template(
        'result.html',
        event=event,
        captured_image=filename,
        matches=matches,
        message=None if matches else "No matching faces found."
    )

if __name__ == '__main__':
    app.run(debug=True)
