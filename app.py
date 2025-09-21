from flask import Flask, render_template, request, jsonify, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
from PIL import Image
from werkzeug.utils import secure_filename
import uuid
import time
import random
import json
from datetime import datetime
from geopy.distance import geodesic

# Import test_model only if needed for X-ray classification
try:
    from test_model import image_classification

    XRAY_CLASSIFICATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: X-ray classification not available: {e}")
    XRAY_CLASSIFICATION_AVAILABLE = False

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-here"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB max file size

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage for active users (in production, use Redis or database)
active_patients = {}  # {patient_id: {sid, location, request_id, status}}
active_drivers = {}  # {driver_id: {sid, location, status, current_request}}
emergency_requests = (
    {}
)  # {request_id: {patient_id, driver_id, status, timestamp, location}}

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api")
def api_documentation():
    """API documentation endpoint"""
    return jsonify(
        {
            "success": True,
            "api_version": "1.0",
            "description": "Ambulance Dispatch System API",
            "websocket_url": f"ws://{request.host}",
            "endpoints": {
                "patient_apis": {
                    "GET /api/patient": "Get patient interface configuration",
                    "POST /api/patient/register": "Register a new patient",
                    "POST /api/patient/emergency": "Create emergency request",
                    "GET /api/patient/status/<patient_id>": "Get patient status",
                },
                "driver_apis": {
                    "GET /api/driver": "Get driver interface configuration",
                    "POST /api/driver/register": "Register a new driver",
                    "GET /api/driver/requests": "Get pending emergency requests",
                    "GET /api/driver/status/<driver_id>": "Get driver status",
                },
                "system_apis": {
                    "GET /api/system/status": "Get system status and statistics"
                },
                "medical_apis": {
                    "POST /upload": "Upload X-ray image",
                    "POST /chest": "Check if image is chest X-ray",
                    "POST /image": "4-class classification (COVID/Normal/Pneumonia/Other)",
                    "POST /iscovid": "2-class COVID detection",
                    "POST /predict": "Mock prediction endpoint",
                },
            },
            "websocket_events": {
                "client_to_server": [
                    "register_patient",
                    "register_driver",
                    "emergency_request",
                    "accept_request",
                    "decline_request",
                    "update_location",
                    "arrived",
                ],
                "server_to_client": [
                    "connected",
                    "patient_registered",
                    "driver_registered",
                    "emergency_alert",
                    "driver_assigned",
                    "request_accepted",
                    "patient_location_update",
                    "driver_location_update",
                    "ambulance_arrived",
                    "driver_disconnected",
                    "no_drivers_available",
                ],
            },
            "example_usage": {
                "patient_flow": [
                    "1. POST /api/patient/register with location",
                    "2. Connect to WebSocket",
                    "3. Send 'register_patient' event",
                    "4. POST /api/patient/emergency to create request",
                    "5. Listen for 'driver_assigned' event",
                    "6. Track driver via 'driver_location_update' events",
                ],
                "driver_flow": [
                    "1. POST /api/driver/register with location",
                    "2. Connect to WebSocket",
                    "3. Send 'register_driver' event",
                    "4. Listen for 'emergency_alert' events",
                    "5. Send 'accept_request' or 'decline_request'",
                    "6. Update location and mark 'arrived'",
                ],
            },
        }
    )


@app.route("/api/patient", methods=["GET", "POST"])
def patient_api():
    if request.method == "GET":
        # Return patient interface configuration
        return jsonify(
            {
                "success": True,
                "interface": "patient",
                "websocket_url": f"ws://{request.host}",
                "endpoints": {
                    "register": "/api/patient/register",
                    "emergency": "/api/patient/emergency",
                    "status": "/api/patient/status",
                },
                "features": [
                    "emergency_request",
                    "location_tracking",
                    "driver_tracking",
                    "real_time_updates",
                ],
            }
        )

    elif request.method == "POST":
        # Handle patient actions via API
        action = request.json.get("action")

        if action == "get_location":
            return jsonify(
                {
                    "success": True,
                    "message": "Use device GPS to get current location",
                    "required_format": {"lat": "number", "lng": "number"},
                }
            )

        return jsonify({"error": "Invalid action"}), 400


@app.route("/api/driver", methods=["GET", "POST"])
def driver_api():
    if request.method == "GET":
        # Return driver interface configuration
        return jsonify(
            {
                "success": True,
                "interface": "driver",
                "websocket_url": f"ws://{request.host}",
                "endpoints": {
                    "register": "/api/driver/register",
                    "status": "/api/driver/status",
                    "requests": "/api/driver/requests",
                },
                "features": [
                    "receive_emergency_alerts",
                    "accept_decline_requests",
                    "location_tracking",
                    "navigation_updates",
                ],
            }
        )

    elif request.method == "POST":
        # Handle driver actions via API
        action = request.json.get("action")

        if action == "get_available_requests":
            # Return pending emergency requests for this driver's area
            available_requests = []
            for request_id, req_data in emergency_requests.items():
                if req_data["status"] == "pending":
                    available_requests.append(
                        {
                            "request_id": request_id,
                            "emergency_type": req_data["emergency_type"],
                            "location": req_data["location"],
                            "timestamp": req_data["timestamp"],
                        }
                    )

            return jsonify({"success": True, "available_requests": available_requests})

        return jsonify({"error": "Invalid action"}), 400


# Patient API endpoints
@app.route("/api/patient/register", methods=["POST"])
def register_patient_api():
    data = request.get_json()
    patient_id = data.get("patient_id", str(uuid.uuid4()))
    location = data.get("location")

    if not location or "lat" not in location or "lng" not in location:
        return jsonify({"error": "Valid location (lat, lng) required"}), 400

    # Store patient info (in real app, save to database)
    patient_data = {
        "patient_id": patient_id,
        "location": location,
        "status": "registered",
        "timestamp": datetime.now().isoformat(),
    }

    return jsonify(
        {
            "success": True,
            "patient_id": patient_id,
            "message": "Patient registered successfully",
            "websocket_events": {
                "connect": "Connect to WebSocket",
                "register_patient": "Send registration data",
                "emergency_request": "Send emergency request",
                "update_location": "Update current location",
            },
        }
    )


@app.route("/api/patient/emergency", methods=["POST"])
def emergency_request_api():
    data = request.get_json()
    patient_id = data.get("patient_id")
    location = data.get("location")
    emergency_type = data.get("emergency_type", "general")

    if not patient_id or not location:
        return jsonify({"error": "Patient ID and location required"}), 400

    # Create emergency request
    request_id = str(uuid.uuid4())
    emergency_data = {
        "request_id": request_id,
        "patient_id": patient_id,
        "location": location,
        "emergency_type": emergency_type,
        "status": "pending",
        "timestamp": datetime.now().isoformat(),
    }

    # Find nearest driver (simplified for API)
    nearest_driver_distance = None
    for driver_id, driver_data in active_drivers.items():
        if driver_data["status"] == "available":
            distance = calculate_distance(location, driver_data["location"])
            if nearest_driver_distance is None or distance < nearest_driver_distance:
                nearest_driver_distance = distance

    return jsonify(
        {
            "success": True,
            "request_id": request_id,
            "status": "pending",
            "nearest_driver_distance": nearest_driver_distance,
            "message": "Emergency request created. Connect to WebSocket for real-time updates.",
            "websocket_events_to_listen": [
                "driver_assigned",
                "driver_location_update",
                "ambulance_arrived",
            ],
        }
    )


@app.route("/api/patient/status/<patient_id>", methods=["GET"])
def get_patient_status(patient_id):
    if patient_id in active_patients:
        patient_data = active_patients[patient_id]
        request_data = None

        if (
            patient_data.get("request_id")
            and patient_data["request_id"] in emergency_requests
        ):
            request_data = emergency_requests[patient_data["request_id"]]

        return jsonify(
            {
                "success": True,
                "patient_id": patient_id,
                "status": patient_data["status"],
                "location": patient_data["location"],
                "current_request": request_data,
            }
        )

    return jsonify({"error": "Patient not found"}), 404


# Driver API endpoints
@app.route("/api/driver/register", methods=["POST"])
def register_driver_api():
    data = request.get_json()
    driver_id = data.get("driver_id", str(uuid.uuid4()))
    location = data.get("location")

    if not location or "lat" not in location or "lng" not in location:
        return jsonify({"error": "Valid location (lat, lng) required"}), 400

    driver_data = {
        "driver_id": driver_id,
        "location": location,
        "status": "available",
        "timestamp": datetime.now().isoformat(),
    }

    return jsonify(
        {
            "success": True,
            "driver_id": driver_id,
            "message": "Driver registered successfully",
            "websocket_events": {
                "connect": "Connect to WebSocket",
                "register_driver": "Send registration data",
                "accept_request": "Accept emergency request",
                "decline_request": "Decline emergency request",
                "update_location": "Update current location",
                "arrived": "Mark as arrived at patient location",
            },
        }
    )


@app.route("/api/driver/requests", methods=["GET"])
def get_driver_requests():
    """Get all pending emergency requests"""
    pending_requests = []

    for request_id, req_data in emergency_requests.items():
        if req_data["status"] == "pending":
            pending_requests.append(
                {
                    "request_id": request_id,
                    "patient_id": req_data["patient_id"],
                    "location": req_data["location"],
                    "emergency_type": req_data["emergency_type"],
                    "timestamp": req_data["timestamp"],
                }
            )

    return jsonify(
        {
            "success": True,
            "pending_requests": pending_requests,
            "total_count": len(pending_requests),
        }
    )


@app.route("/api/driver/status/<driver_id>", methods=["GET"])
def get_driver_status(driver_id):
    if driver_id in active_drivers:
        driver_data = active_drivers[driver_id]
        current_request = None

        if (
            driver_data.get("current_request")
            and driver_data["current_request"] in emergency_requests
        ):
            current_request = emergency_requests[driver_data["current_request"]]

        return jsonify(
            {
                "success": True,
                "driver_id": driver_id,
                "status": driver_data["status"],
                "location": driver_data["location"],
                "current_request": current_request,
            }
        )

    return jsonify({"error": "Driver not found"}), 404


@app.route("/api/system/status", methods=["GET"])
def get_system_status():
    """Get overall system status"""
    return jsonify(
        {
            "success": True,
            "system_status": "online",
            "active_patients": len(active_patients),
            "active_drivers": len(active_drivers),
            "pending_requests": len(
                [r for r in emergency_requests.values() if r["status"] == "pending"]
            ),
            "total_requests": len(emergency_requests),
            "websocket_url": f"ws://{request.host}",
            "api_endpoints": {
                "patient": {
                    "register": "/api/patient/register",
                    "emergency": "/api/patient/emergency",
                    "status": "/api/patient/status/<patient_id>",
                },
                "driver": {
                    "register": "/api/driver/register",
                    "requests": "/api/driver/requests",
                    "status": "/api/driver/status/<driver_id>",
                },
                "system": {"status": "/api/system/status"},
            },
        }
    )


# Keep web interfaces for testing/demo purposes
@app.route("/patient")
def patient_interface():
    return render_template("patient.html")


@app.route("/driver")
def driver_interface():
    return render_template("driver.html")


# WebSocket event handlers
@socketio.on("connect")
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit("connected", {"message": "Connected to ambulance dispatch system"})


@socketio.on("disconnect")
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    # Remove user from active lists
    for patient_id, patient_data in list(active_patients.items()):
        if patient_data["sid"] == request.sid:
            del active_patients[patient_id]
            break

    for driver_id, driver_data in list(active_drivers.items()):
        if driver_data["sid"] == request.sid:
            # If driver was on a request, notify patient
            if driver_data.get("current_request"):
                request_id = driver_data["current_request"]
                if request_id in emergency_requests:
                    patient_id = emergency_requests[request_id]["patient_id"]
                    if patient_id in active_patients:
                        socketio.emit(
                            "driver_disconnected",
                            {"message": "Driver disconnected, finding new driver"},
                            room=active_patients[patient_id]["sid"],
                        )
            del active_drivers[driver_id]
            break


@socketio.on("register_patient")
def handle_register_patient(data):
    patient_id = data.get("patient_id", str(uuid.uuid4()))
    location = data.get("location")

    active_patients[patient_id] = {
        "sid": request.sid,
        "location": location,
        "request_id": None,
        "status": "available",
    }

    emit("patient_registered", {"patient_id": patient_id, "status": "registered"})
    print(f"Patient registered: {patient_id}")


@socketio.on("register_driver")
def handle_register_driver(data):
    driver_id = data.get("driver_id", str(uuid.uuid4()))
    location = data.get("location")

    active_drivers[driver_id] = {
        "sid": request.sid,
        "location": location,
        "status": "available",
        "current_request": None,
    }

    emit("driver_registered", {"driver_id": driver_id, "status": "registered"})
    print(f"Driver registered: {driver_id}")


@socketio.on("emergency_request")
def handle_emergency_request(data):
    patient_id = data.get("patient_id")
    location = data.get("location")
    emergency_type = data.get("emergency_type", "general")

    if patient_id not in active_patients:
        emit("error", {"message": "Patient not registered"})
        return

    # Create emergency request
    request_id = str(uuid.uuid4())
    emergency_requests[request_id] = {
        "patient_id": patient_id,
        "driver_id": None,
        "status": "pending",
        "timestamp": datetime.now().isoformat(),
        "location": location,
        "emergency_type": emergency_type,
    }

    # Update patient status
    active_patients[patient_id]["request_id"] = request_id
    active_patients[patient_id]["status"] = "requesting"
    active_patients[patient_id]["location"] = location

    # Find nearest available driver
    nearest_driver = find_nearest_driver(location)

    if nearest_driver:
        driver_id, driver_data = nearest_driver
        # Notify driver about emergency request
        socketio.emit(
            "emergency_alert",
            {
                "request_id": request_id,
                "patient_location": location,
                "emergency_type": emergency_type,
                "distance": calculate_distance(location, driver_data["location"]),
            },
            room=driver_data["sid"],
        )

        emit(
            "request_sent",
            {
                "request_id": request_id,
                "message": "Emergency request sent to nearest driver",
                "driver_found": True,
            },
        )
    else:
        emit(
            "request_sent",
            {
                "request_id": request_id,
                "message": "No drivers available, you are in queue",
                "driver_found": False,
            },
        )


@socketio.on("accept_request")
def handle_accept_request(data):
    driver_id = data.get("driver_id")
    request_id = data.get("request_id")

    if driver_id not in active_drivers or request_id not in emergency_requests:
        emit("error", {"message": "Invalid driver or request"})
        return

    request_data = emergency_requests[request_id]
    if request_data["status"] != "pending":
        emit("error", {"message": "Request no longer available"})
        return

    # Update request and driver status
    emergency_requests[request_id]["driver_id"] = driver_id
    emergency_requests[request_id]["status"] = "accepted"

    active_drivers[driver_id]["current_request"] = request_id
    active_drivers[driver_id]["status"] = "en_route"

    patient_id = request_data["patient_id"]
    active_patients[patient_id]["status"] = "driver_assigned"

    # Notify patient
    patient_sid = active_patients[patient_id]["sid"]
    socketio.emit(
        "driver_assigned",
        {
            "driver_id": driver_id,
            "driver_location": active_drivers[driver_id]["location"],
            "estimated_arrival": "5-10 minutes",  # This could be calculated based on distance
        },
        room=patient_sid,
    )

    # Confirm to driver
    emit(
        "request_accepted",
        {"request_id": request_id, "patient_location": request_data["location"]},
    )


@socketio.on("decline_request")
def handle_decline_request(data):
    driver_id = data.get("driver_id")
    request_id = data.get("request_id")

    # Find next nearest driver
    if request_id in emergency_requests:
        request_data = emergency_requests[request_id]
        patient_location = request_data["location"]

        # Find next nearest driver (excluding current driver)
        next_driver = find_nearest_driver(patient_location, exclude_driver=driver_id)

        if next_driver:
            next_driver_id, next_driver_data = next_driver
            socketio.emit(
                "emergency_alert",
                {
                    "request_id": request_id,
                    "patient_location": patient_location,
                    "emergency_type": request_data["emergency_type"],
                    "distance": calculate_distance(
                        patient_location, next_driver_data["location"]
                    ),
                },
                room=next_driver_data["sid"],
            )
        else:
            # No more drivers available
            patient_id = request_data["patient_id"]
            if patient_id in active_patients:
                socketio.emit(
                    "no_drivers_available",
                    {"message": "No drivers available at the moment, please try again"},
                    room=active_patients[patient_id]["sid"],
                )


@socketio.on("update_location")
def handle_location_update(data):
    user_id = data.get("user_id")
    location = data.get("location")
    user_type = data.get("user_type")  # 'patient' or 'driver'

    if user_type == "patient" and user_id in active_patients:
        active_patients[user_id]["location"] = location

        # If patient has an assigned driver, update driver with new location
        request_id = active_patients[user_id].get("request_id")
        if request_id and request_id in emergency_requests:
            driver_id = emergency_requests[request_id].get("driver_id")
            if driver_id and driver_id in active_drivers:
                socketio.emit(
                    "patient_location_update",
                    {"patient_location": location},
                    room=active_drivers[driver_id]["sid"],
                )

    elif user_type == "driver" and user_id in active_drivers:
        active_drivers[user_id]["location"] = location

        # If driver has a current request, update patient with driver location
        request_id = active_drivers[user_id].get("current_request")
        if request_id and request_id in emergency_requests:
            patient_id = emergency_requests[request_id]["patient_id"]
            if patient_id in active_patients:
                socketio.emit(
                    "driver_location_update",
                    {"driver_location": location},
                    room=active_patients[patient_id]["sid"],
                )


@socketio.on("arrived")
def handle_arrived(data):
    driver_id = data.get("driver_id")

    if driver_id not in active_drivers:
        emit("error", {"message": "Driver not found"})
        return

    request_id = active_drivers[driver_id].get("current_request")
    if request_id and request_id in emergency_requests:
        patient_id = emergency_requests[request_id]["patient_id"]

        # Update status
        emergency_requests[request_id]["status"] = "arrived"
        active_drivers[driver_id]["status"] = "arrived"
        active_patients[patient_id]["status"] = "ambulance_arrived"

        # Notify patient
        socketio.emit(
            "ambulance_arrived",
            {"message": "Ambulance has arrived at your location"},
            room=active_patients[patient_id]["sid"],
        )

        emit("arrival_confirmed", {"message": "Arrival confirmed"})


def find_nearest_driver(patient_location, exclude_driver=None):
    """Find the nearest available driver to the patient location"""
    nearest_driver = None
    min_distance = float("inf")

    for driver_id, driver_data in active_drivers.items():
        if driver_id == exclude_driver:
            continue

        if driver_data["status"] == "available":
            distance = calculate_distance(patient_location, driver_data["location"])
            if distance < min_distance:
                min_distance = distance
                nearest_driver = (driver_id, driver_data)

    return nearest_driver


def calculate_distance(loc1, loc2):
    """Calculate distance between two locations in kilometers"""
    try:
        if isinstance(loc1, dict) and isinstance(loc2, dict):
            point1 = (loc1["lat"], loc1["lng"])
            point2 = (loc2["lat"], loc2["lng"])
            return geodesic(point1, point2).kilometers
        return 0
    except:
        return 0


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
    if not XRAY_CLASSIFICATION_AVAILABLE:
        return jsonify({"error": "X-ray classification not available"}), 503

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
    if not XRAY_CLASSIFICATION_AVAILABLE:
        return jsonify({"error": "X-ray classification not available"}), 503

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
    if not XRAY_CLASSIFICATION_AVAILABLE:
        return jsonify({"error": "X-ray classification not available"}), 503

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
    socketio.run(app, debug=True, host="0.0.0.0", port=8080)
