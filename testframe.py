import os
import asyncio
import json
import requests
import base64
from datetime import datetime
from frame_sdk import Frame
from frame_sdk.camera import AutofocusType, Quality
from geopy.geocoders import Nominatim


# Function to capture photo and save it
async def capture_photo():
    """
    Captures a photo using the Frame device.
    """
    photo_path = "captured_photo.jpg"
    async with Frame() as f:
        await f.camera.save_photo(
            photo_path,
            quality=Quality.HIGH,
            autofocus_seconds=2,
            autofocus_type=AutofocusType.CENTER_WEIGHTED,
        )
    print(f"Photo saved at: {photo_path}")
    return photo_path


# Function to retrieve the current location
def get_location():
    """
    Get the geolocation (latitude, longitude) of the current device.
    """
    try:
        response = requests.get("https://ipinfo.io/json").json()
        loc = response.get("loc")
        if loc:
            latitude, longitude = map(float, loc.split(","))
            print(f"Location: Latitude {latitude}, Longitude {longitude}")
            return latitude, longitude
    except Exception as e:
        print(f"Error fetching location: {e}")
    return None, None


# Function to generate captions using LLaVA
def generate_caption(image_path):
    """
    Sends the image to the LLaVA model to generate a caption.
    """
    url = "http://localhost:11434/api/generate"
    with open(image_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

    payload = {"model": "llava", "prompt": "What's in this image?", "images": [img_base64]}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)
        caption = ""
        for line in response.iter_lines():
            if line:
                json_line = json.loads(line.decode("utf-8"))
                caption += json_line.get("response", "")
        print(f"Generated Caption: {caption.strip()}")
        return caption.strip()
    except Exception as e:
        print(f"Error generating caption: {e}")
        return "No caption available."


# Function to save metadata to a JSON file
def save_metadata(image_path, latitude, longitude, caption):
    """
    Saves the image metadata (location, caption, image path) to a JSON file.
    """
    metadata_file = "photo_metadata.json"
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "image_path": image_path,
        "latitude": latitude,
        "longitude": longitude,
        "caption": caption,
    }

    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as file:
            data = json.load(file)
    else:
        data = []

    data.append(metadata)

    with open(metadata_file, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Metadata saved to {metadata_file}")


# Main function
async def main():
    print("Starting photo capture...")
    image_path = await capture_photo()

    latitude, longitude = get_location()
    if not latitude or not longitude:
        print("Unable to fetch location. Aborting...")
        return

    caption = generate_caption(image_path)
    save_metadata(image_path, latitude, longitude, caption)


if __name__ == "__main__":
    asyncio.run(main())
