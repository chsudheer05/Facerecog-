import os
from flask import Flask, render_template, request
import face_recognition
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Set folders
UPLOAD_FOLDER = 'static/uploads'
KNOWN_FACES_DIR = 'static/photos'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load known faces
known_faces = []  # List of (encoding, filename)

for filename in os.listdir(KNOWN_FACES_DIR):
    filepath = os.path.join(KNOWN_FACES_DIR, filename)
    image = face_recognition.load_image_file(filepath)
    encodings = face_recognition.face_encodings(image)
    for encoding in encodings:
        known_faces.append((encoding, filename))  # Keep all encodings

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files and 'image' not in request.form:
        return "No image uploaded", 400

    # Support both file upload and base64 (camera)
    if 'image' in request.files:
        file = request.files['image']
        if file.filename == '':
            return "No selected file", 400
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
    else:
        import base64
        from io import BytesIO
        from PIL import Image
        data_url = request.form['image']
        header, encoded = data_url.split(',', 1)
        image_data = base64.b64decode(encoded)
        img = Image.open(BytesIO(image_data))
        filename = 'captured.jpg'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        img.save(filepath)

    uploaded_image = face_recognition.load_image_file(filepath)
    uploaded_encodings = face_recognition.face_encodings(uploaded_image)

    if not uploaded_encodings:
        return render_template('result.html', matches=[], message="No face detected in uploaded image.")

    uploaded_encoding = uploaded_encodings[0]
    threshold = 0.5
    matches = set()  # Avoid duplicates

    for known_encoding, known_filename in known_faces:
        distance = face_recognition.face_distance([known_encoding], uploaded_encoding)[0]
        if distance < threshold:
            matches.add(known_filename)

    return render_template('result.html', matches=list(matches), message=None if matches else "No matching faces found.")

if __name__ == '__main__':
    app.run(debug=True)
