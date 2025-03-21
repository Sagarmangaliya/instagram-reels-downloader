from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import os
import logging
import requests
from bs4 import BeautifulSoup

# Create the Flask app instance
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
        # Extract shortcode from URL
        shortcode = reel_url.strip("/").split("/")[-1].split('?')[0]
        logging.debug(f"Extracted shortcode: {shortcode}")

        # Prepare data and headers for saveig.app API
        post_data = {
            'q': reel_url,
            't': 'media',
            'lang': 'en'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        # Send POST request to saveig.app
        response = requests.post('https://saveig.app/api/ajaxsearch', data=post_data, headers=headers)
        if response.status_code != 200:
            logging.error(f"Failed to fetch download link: {response.status_code}")
            return jsonify({"error": "Failed to fetch download link"}), 500

        response_json = response.json()
        if not response_json.get("data"):
            logging.error("No data received from saveig.app")
            return jsonify({"error": "No data received from saveig.app"}), 500

        # Parse HTML to get download link
        soup = BeautifulSoup(response_json['data'], 'html.parser')
        download_btn = soup.select_one('.download-items__btn a')
        if not download_btn:
            logging.error("Download button not found")
            return jsonify({"error": "Download button not found"}), 500

        download_link = download_btn.get('href')
        if not download_link:
            logging.error("Download link not found")
            return jsonify({"error": "Download link not found"}), 500

        # Download the video
        video_response = requests.get(download_link, headers=headers, stream=True)
        if video_response.status_code != 200:
            logging.error(f"Failed to download video: {video_response.status_code}")
            return jsonify({"error": "Failed to download video"}), 500

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
        logging.error(f"Error in download_reel: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/downloads/<filename>")
def serve_video(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use PORT if provided, otherwise default to 5000
    app.run(host="0.0.0.0", port=port, debug=False)  # Set debug=False for production
