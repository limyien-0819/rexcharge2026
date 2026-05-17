import requests
import base64

# 1. Put the name of your test picture here
image_path = "test_picture.jpg"

# 2. Read the image and convert it to Base64
with open(image_path, "rb") as image_file:
    img_str = base64.b64encode(image_file.read()).decode("ascii")

# 3. Your exact API key and endpoint
url = "https://detect.roboflow.com/recharge-2/5?api_key=vrJ7tThB8mOBHDvY68Mj&confidence=1"

print("Sending to Roboflow...")

# 4. Send to Roboflow
resp = requests.post(url, data=img_str, headers={"Content-Type": "application/x-www-form-urlencoded"})

# 5. Print the raw truth
print("STATUS CODE:", resp.status_code)
print("RESPONSE:", resp.json())