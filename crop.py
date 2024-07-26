from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import cv2

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        return jsonify({"filename": filename, "filepath": filepath}), 200

@app.route('/crop', methods=['POST'])
def crop_video():
    data = request.json
    input_path = data['filepath']
    x = data['x']
    y = data['y']
    width = data['width']
    height = data['height']

    # Verify if the file exists
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    cap = cv2.VideoCapture(input_path)

    # Check if the video was opened successfully
    if not cap.isOpened():
        return jsonify({'error': 'Could not open video file'}), 400

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Verify if video properties were read correctly
    if frame_width == 0 or frame_height == 0 or fps == 0 or total_frames == 0:
        return jsonify({'error': 'Failed to read video properties'}), 400

    # Set up output video writer
    output_path = os.path.join(UPLOAD_FOLDER, 'output_cropped.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Read frames and write cropped video
    # while cap.isOpened():
    #     ret, frame = cap.read()
    #     if not ret:
    #         break
    #     cropped_frame = frame[y:y + height, x:x + width]
    #     out.write(cropped_frame)
    max_frames = int(fps * 60)

    frame_count = 0
    while cap.isOpened() and frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        cropped_frame = frame[y:y + height, x:x + width]
        out.write(cropped_frame)
        frame_count += 1

    cap.release()
    out.release()

    return send_file(output_path, as_attachment=True)

  

if __name__ == '__main__':
    app.run(debug=True)