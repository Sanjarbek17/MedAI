from flask import Flask, render_template, request, jsonify, url_for
import os
from PIL import Image
from werkzeug.utils import secure_filename
import uuid
import time
import random

from test_model import image_classification

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-here"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = str(uuid.uuid4()) + "." + file.filename.rsplit(".", 1)[1].lower()
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        return jsonify(
            {
                "success": True,
                "filename": filename,
                "message": "File uploaded successfully",
            }
        )

    return (
        jsonify(
            {"error": "Invalid file type. Please upload JPG, JPEG, or PNG files only"}
        ),
        400,
    )


@app.route("/image", methods=["POST"])
def image():
    image = request.files["file"]
    # Your  model trained with 4 classes is path
    model_path = "models/four_classes.pt"
    image_data = Image.open(image.stream)

    clasification_image = image_classification(model_path=model_path, image=image_data)

    return clasification_image


@app.route("/iscovid", methods=["POST"])
def iscovid_check():
    image = request.files["file"]
    # Your  model trained with 2 classes is path (check Covid).
    model_path = "models/is_covid.pt"
    image_data = Image.open(image.stream)

    clasification_image = image_classification(model_path=model_path, image=image_data)

    return clasification_image


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    filename = data.get("filename")

    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    # Simulate processing time
    time.sleep(2)

    # Mock prediction results (replace with actual AI model)
    mock_results = [
        {"class": "Normal", "confidence": 94, "covid": 3, "normal": 94, "pneumonia": 3},
        {
            "class": "COVID-19",
            "confidence": 87,
            "covid": 87,
            "normal": 8,
            "pneumonia": 5,
        },
        {
            "class": "Pneumonia",
            "confidence": 91,
            "covid": 4,
            "normal": 5,
            "pneumonia": 91,
        },
    ]

    result = random.choice(mock_results)

    return jsonify({"success": True, "prediction": result})


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return url_for("static", filename="uploads/" + filename)


if __name__ == "__main__":
    # Create uploads directory if it doesn't exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=8080)
