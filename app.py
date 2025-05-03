# At the top of app.py
import os
import cv2
import base64
import json
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime

# Directory setup
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/registered_faces", exist_ok=True)
os.makedirs("known_faces", exist_ok=True)


app = Flask(__name__)
app.secret_key = "face_recognition_attendance_system"  # Added secret key for flash messages
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DEEPSTACK_URL = "http://localhost:5000/v1/vision/face/recognize"
REGISTERED_FACE_FOLDER = "known_faces"
ATTENDANCE_LOG = "attendance.csv"

# Register known faces (once at startup)
def register_known_faces():
    registered_count = 0
    for filename in os.listdir(REGISTERED_FACE_FOLDER):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            name = os.path.splitext(filename)[0]
            with open(os.path.join(REGISTERED_FACE_FOLDER, filename), "rb") as f:
                response = requests.post(
                    "http://localhost:5000/v1/vision/face/register",
                    files={"image": f},
                    data={"userid": name}
                )
                if response.status_code == 200:
                    registered_count += 1
    print(f"Registered {registered_count} faces at startup.")

# Function to ensure attendance log file exists with headers
def initialize_attendance_log():
    if not os.path.exists(ATTENDANCE_LOG):
        with open(ATTENDANCE_LOG, "w") as f:
            f.write("Name,Timestamp,Class\n")
    
@app.route("/", methods=["GET", "POST"])
def index():
    recognized_name = None
    if request.method == "POST":
        file = request.files["image"]
        if file:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            with open(filepath, "rb") as f:
                response = requests.post(
                    DEEPSTACK_URL,
                    files={"image": f}
                ).json()

            if response.get("success") and response.get("predictions"):
                recognized_name = response["predictions"][0]["userid"]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Get class information from users.json if available
                classroom = get_user_class(recognized_name)
                
                with open(ATTENDANCE_LOG, "a") as f:
                    f.write(f"{recognized_name},{timestamp},{classroom}\n")

    return render_template("index.html", name=recognized_name)

def get_user_class(username):
    """Get the class information for a user from users.json"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            try:
                users = json.load(f)
                return users.get(username, "Unknown")
            except json.JSONDecodeError:
                return "Unknown"
    return "Unknown"

USERS_FILE = "users.json"
def save_user(username, classroom):
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            try:
                users = json.load(f)
            except json.JSONDecodeError:
                users = {}  # File is empty or invalid

    users[username] = classroom
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)
    return True

@app.route("/attendance")
def attendance_interface():
    return render_template("attendance.html")

@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    data = request.get_json()
    img_data = data["image_data"]
    header, encoded = img_data.split(",", 1)
    image_bytes = base64.b64decode(encoded)
    temp_path = "static/uploads/temp.png"
    with open(temp_path, "wb") as f:
        f.write(image_bytes)

    with open(temp_path, "rb") as f:
        response = requests.post(
            "http://localhost:5000/v1/vision/face/recognize",
            files={"image": f}
        ).json()

    if response.get("success") and response.get("predictions"):
        # Check if face is recognized with confidence
        if response["predictions"][0].get("userid") and response["predictions"][0].get("userid") != "unknown":
            name = response["predictions"][0]["userid"]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Get class information from users.json if available
            classroom = get_user_class(name)
            
            # Write to attendance log
            with open(ATTENDANCE_LOG, "a") as f:
                f.write(f"{name},{timestamp},{classroom}\n")
                
            return {"status": "marked", "name": name, "class": classroom}
        else:
            # Face detected but not recognized/registered
            return {"status": "unknown_face", "message": "Face detected but not recognized"}
    return {"status": "no_face", "message": "No face detected"}

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        classroom = request.form["classroom"]
        img_data = request.form["image_data"]

        # Decode base64 image
        header, encoded = img_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        
        # Save to both locations for redundancy
        registered_path = f"static/registered_faces/{username}.png"
        known_faces_path = f"known_faces/{username}.jpg"
        
        with open(registered_path, "wb") as f:
            f.write(image_bytes)
            
        with open(known_faces_path, "wb") as f:
            f.write(image_bytes)

        # Register face with DeepStack
        try:
            with open(registered_path, "rb") as f:
                response = requests.post(
                    "http://localhost:5000/v1/vision/face/register",
                    files={"image": f},
                    data={"userid": username}
                )
                
            if response.status_code != 200:
                return f"Error registering with face recognition service: {response.text}", 500
                
            # Save user information
            if save_user(username, classroom):
                return f"User {username} registered in class {classroom}."
            else:
                return "Error saving user information", 500
                
        except Exception as e:
            return f"Error: {str(e)}", 500

    return render_template("register.html")

@app.route("/view_attendance")
def view_attendance():
    attendances = []
    if os.path.exists(ATTENDANCE_LOG):
        with open(ATTENDANCE_LOG, "r") as f:
            lines = f.readlines()
            # Skip header row
            if len(lines) > 1:
                for line in lines[1:]:
                    parts = line.strip().split(",")
                    if len(parts) >= 2:
                        name = parts[0]
                        timestamp = parts[1]
                        classroom = parts[2] if len(parts) > 2 else "Unknown"
                        attendances.append({
                            "name": name,
                            "timestamp": timestamp,
                            "class": classroom
                        })
    
    return jsonify({"attendances": attendances})
  
if __name__ == "__main__":
    initialize_attendance_log()
    register_known_faces()
    app.run(debug=True)
