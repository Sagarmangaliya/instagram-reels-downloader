import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from urllib.parse import urlparse
from instagrapi import Client

app = Flask(__name__)

# Directory to store downloaded files
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Initialize Instagrapi client
client = Client()

# Logging setup
logging.basicConfig(level=logging.DEBUG)

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Instagram Downloader</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                text-align: center;
                padding: 50px;
            }
            .container {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                max-width: 500px;
                margin: 0 auto;
            }
            input, button {
                width: 100%;
                padding: 10px;
                margin-top: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            button {
                background: #007bff;
                color: white;
                cursor: pointer;
            }
            button:hover {
                background: #0056b3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Instagram Reels Downloader</h1>
            <input type="text" id="reelURL" placeholder="Paste Instagram Reel URL here..." />
            <button onclick="downloadReel()">Download</button>
            <p id="result"></p>
        </div>

        <script>
            function downloadReel() {
                let url = document.getElementById("reelURL").value;
                if (!url) {
                    alert("Please enter a valid Instagram Reel URL!");
                    return;
                }

                fetch("/download", {
                    method: "POST",
                    body: JSON.stringify({ reel_url: url }),
                    headers: { "Content-Type": "application/json" },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.download_url) {
                        document.getElementById("result").innerHTML = 
                            `<a href="${data.download_url}" download>Click here to download</a>`;
                    } else {
                        document.getElementById("result").innerText = "Download failed!";
                    }
                })
                .catch(error => console.error("Error:", error));
            }
        </script>
    </body>
    </html>
    """

@app.route("/download", methods=["POST"])
def download_reel():
    logging.debug("Received download request")
    data = request.get_json()
    reel_url = data.get("reel_url")
    logging.debug(f"Reel URL: {reel_url}")

    if not reel_url:
        return jsonify({"error": "Missing reel_url"}), 400

    try:
        # Extract shortcode from the URL
        parsed_url = urlparse(reel_url)
        shortcode = parsed_url.path.strip("/").split("/")[-1]
        logging.debug(f"Extracted shortcode: {shortcode}")

        # Fetch media info using Instagrapi
        media = client.media_pk_from_code(shortcode)
        media_info = client.media_info(media)
        logging.debug(f"Media info: {media_info}")

        # Get the video URL
        video_url = media_info.video_url
        logging.debug(f"Video URL: {video_url}")

        # Download the video
        video_filename = f"{shortcode}.mp4"
        video_path = os.path.join(DOWNLOAD_FOLDER, video_filename)
        client.video_download(video_url, video_path)
        logging.debug(f"Video downloaded to: {video_path}")

        # Return the video URL
        return jsonify({
            "message": "Download successful",
            "download_url": f"/downloads/{video_filename}"
        })

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/downloads/<filename>")
def serve_video(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use PORT if provided, otherwise default to 5000
    app.run(host="0.0.0.0", port=port, debug=False)  # Set debug=False for production
