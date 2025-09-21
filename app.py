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


@app.route("/chest", methods=["POST"])
def chest_check():
    image = request.files["file"]
    # Model to check if image is a chest X-ray
    model_path = "models/only_chest.pt"
    image_data = Image.open(image.stream)

    # Get classification results
    clasification_result = image_classification(model_path=model_path, image=image_data)

    # Parse the JSON string returned by image_classification
    import json

    classification_data = json.loads(clasification_result)

    # Transform to match predict endpoint format
    if classification_data and len(classification_data) > 0:
        top_prediction = classification_data[0]  # Get the highest confidence prediction

        # Create prediction object matching predict endpoint format
        prediction = {
            "class": top_prediction["label"],
            "confidence": int(
                top_prediction["confidence"] * 100
            ),  # Convert to percentage
        }

        # For chest validation, we don't need covid/normal/pneumonia breakdown
        # Just return whether it's chest or not
        prediction["covid"] = 0
        prediction["normal"] = 0
        prediction["pneumonia"] = 0

        return jsonify({"success": True, "prediction": prediction})
    else:
        return jsonify({"error": "No classification results"}), 500


@app.route("/image", methods=["POST"])
def image():
    image = request.files["file"]
    # Your  model trained with 4 classes is path
    model_path = "models/four_classes.pt"
    image_data = Image.open(image.stream)

    # Get classification results
    clasification_result = image_classification(model_path=model_path, image=image_data)

    # Parse the JSON string returned by image_classification
    import json

    classification_data = json.loads(clasification_result)

    # Transform to match predict endpoint format
    if classification_data and len(classification_data) > 0:
        top_prediction = classification_data[0]  # Get the highest confidence prediction

        # Create prediction object matching predict endpoint format
        prediction = {
            "class": top_prediction["label"],
            "confidence": int(
                top_prediction["confidence"] * 100
            ),  # Convert to percentage
        }

        # Add individual class confidences (initialize to 0)
        prediction["covid"] = 0
        prediction["normal"] = 0
        prediction["pneumonia"] = 0

        # Set the confidence for the predicted class
        class_name = top_prediction["label"].lower()
        if "covid" in class_name:
            prediction["covid"] = prediction["confidence"]
        elif "normal" in class_name:
            prediction["normal"] = prediction["confidence"]
        elif "pneumonia" in class_name:
            prediction["pneumonia"] = prediction["confidence"]

        # Distribute remaining confidence among other classes based on other predictions
        remaining_confidence = 100 - prediction["confidence"]
        other_predictions = (
            classification_data[1:3] if len(classification_data) > 1 else []
        )

        for pred in other_predictions:
            pred_class = pred["label"].lower()
            pred_conf = int(pred["confidence"] * 100)
            if "covid" in pred_class and prediction["covid"] == 0:
                prediction["covid"] = min(pred_conf, remaining_confidence)
                remaining_confidence -= prediction["covid"]
            elif "normal" in pred_class and prediction["normal"] == 0:
                prediction["normal"] = min(pred_conf, remaining_confidence)
                remaining_confidence -= prediction["normal"]
            elif "pneumonia" in pred_class and prediction["pneumonia"] == 0:
                prediction["pneumonia"] = min(pred_conf, remaining_confidence)
                remaining_confidence -= prediction["pneumonia"]

        return jsonify({"success": True, "prediction": prediction})
    else:
        return jsonify({"error": "No classification results"}), 500


@app.route("/iscovid", methods=["POST"])
def iscovid_check():
    image = request.files["file"]
    # Your  model trained with 2 classes is path (check Covid).
    model_path = "models/is_covid.pt"
    image_data = Image.open(image.stream)

    # Get classification results
    clasification_result = image_classification(model_path=model_path, image=image_data)

    # Parse the JSON string returned by image_classification
    import json

    classification_data = json.loads(clasification_result)

    # Transform to match predict endpoint format
    if classification_data and len(classification_data) > 0:
        top_prediction = classification_data[0]  # Get the highest confidence prediction

        # Create prediction object matching predict endpoint format
        prediction = {
            "class": top_prediction["label"],
            "confidence": int(
                top_prediction["confidence"] * 100
            ),  # Convert to percentage
        }

        # For COVID detection model, set COVID vs Normal
        prediction["covid"] = 0
        prediction["normal"] = 0
        prediction["pneumonia"] = 0  # Keep for consistency

        # Set the confidence for the predicted class
        class_name = top_prediction["label"].lower()
        if "covid" in class_name:
            prediction["covid"] = prediction["confidence"]
            # Set normal as the complement for binary classification
            if len(classification_data) > 1:
                prediction["normal"] = int(classification_data[1]["confidence"] * 100)
            else:
                prediction["normal"] = 100 - prediction["confidence"]
        else:
            prediction["normal"] = prediction["confidence"]
            # Set covid as the complement for binary classification
            if len(classification_data) > 1:
                prediction["covid"] = int(classification_data[1]["confidence"] * 100)
            else:
                prediction["covid"] = 100 - prediction["confidence"]

        return jsonify({"success": True, "prediction": prediction})
    else:
        return jsonify({"error": "No classification results"}), 500


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
