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

# Load session from file
try:
    loader.load_session_from_file("rahulsnid", "session")
except Exception as e:
    logging.error(f"Failed to load session: {e}")

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

                fetch("https://instagram-reels-downloader-iqb9.onrender.com/download/download", {
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

@app.route("https://instagram-reels-downloader-iqb9.onrender.com/download", methods=["POST"])
def download_reel():
    logging.debug("Received download request")
    data = request.get_json()
    reel_url = data.get("reel_url")
    logging.debug(f"Reel URL:
