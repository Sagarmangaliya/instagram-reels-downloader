import os
import logging
import instaloader
from flask import Flask, request, jsonify, send_from_directory
from urllib.parse import urlparse

app = Flask(__name__)

# Directory to store downloaded files
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Initialize Instaloader
loader = instaloader.Instaloader()

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
        <title>Instagram Reels Downloader</title>
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
        # Remove query parameters from the URL
        parsed_url = urlparse(reel_url)
        clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        logging.debug(f"Cleaned URL: {clean_url}")

        # Extract shortcode from the cleaned URL
        shortcode = clean_url.strip("/").split("/")[-1]
        logging.debug(f"Extracted shortcode: {shortcode}")

        # Download the reel
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        logging.debug(f"Post object created: {post}")

        loader.download_post(post, target=DOWNLOAD_FOLDER)
        logging.debug("Reel downloaded successfully")

        # Find the downloaded file
        video_file = next((f for f in os.listdir(DOWNLOAD_FOLDER) if shortcode in f and f.endswith(".mp4")), None)
        logging.debug(f"Found video file: {video_file}")

        if not video_file:
            return jsonify({"error": "Failed to download the video"}), 500

        # Return the video URL
        return jsonify({
            "message": "Download successful",
            "download_url": f"/downloads/{video_file}"
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
