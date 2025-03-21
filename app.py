import os
import logging
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Directory to store downloaded videos
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Logging setup
logging.basicConfig(level=logging.DEBUG)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download_reel():
    logging.debug("Received download request")
    data = request.get_json()
    reel_url = data.get("reel_url")
    logging.debug(f"Reel URL: {reel_url}")

    if not reel_url:
        return jsonify({"error": "Missing reel_url"}), 400

    try:
        # Extract short code from URL
        shortcode = reel_url.strip("/").split("/")[-1].split('?')[0]
        logging.debug(f"Extracted shortcode: {shortcode}")

        # Prepare data and headers for saveig.app API
        post_data = {
            'q': reel_url,
            't': 'media',
            'lang': 'en'
        }
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://saveig.app',
            'Referer': 'https://saveig.app/en',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }

        # Send POST request to saveig.app
        response = requests.post('https://wp-json/visolix/api/download', data=post_data, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        html_content = response_json.get('data', '')
        if not html_content:
            raise ValueError("No data received from saveig.app")

        # Parse HTML to get download link
        soup = BeautifulSoup(html_content, 'html.parser')
        download_btn = soup.select_one('.download-items__btn a')
        if not download_btn:
            raise ValueError("Download button not found")
        download_link = download_btn.get('href')
        if not download_link:
            raise ValueError("Download link not found")

        # Download the video
        video_headers = {
            'Referer': 'https://saveig.app/',
            'User-Agent': headers['User-Agent']
        }
        video_response = requests.get(download_link, headers=video_headers, stream=True)
        video_response.raise_for_status()

        # Save the video
        filename = f"{shortcode}.mp4"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        with open(filepath, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Return the download URL
        return jsonify({
            "message": "Download successful",
            "download_url": f"/downloads/{filename}"
        })

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/downloads/<filename>")
def serve_video(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
