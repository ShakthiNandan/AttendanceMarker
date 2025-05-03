import requests

def recognize_face(image_path):
    url = "http://localhost:5000/v1/vision/face/recognize"
    with open(image_path, "rb") as f:
        response = requests.post(url, files={"image": f})
    return response.json()

result = recognize_face("Shakthi.jpg")
if result["success"] and result["predictions"]:
    user_id = result["predictions"][0]["userid"]
    print(f"{user_id} is present ✅")
else:
    print("No known face detected ❌")
