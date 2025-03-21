import requests
import logging
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

logging.basicConfig(level=logging.DEBUG)

def download_reel(reel_url):
    try:
        # Ensure the URL is complete
        api_url = "https://saveig.in/wp-json/visolix/api/download"
        data = {
            "q": reel_url,
            "t": "media",
            "lang": "en",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        logging.debug(f"Making request to: {api_url}")
        response = requests.post(api_url, data=data, headers=headers)
        if response.status_code != 200:
            logging.error(f"API returned status code: {response.status_code}")
            logging.error(f"API response: {response.text}")
            return {"error": "Failed to fetch download link"}, 500

        response_json = response.json()
        logging.debug(f"API Response: {response_json}")

        if not response_json.get("data"):
            logging.error("No data received from the service")
            return {"error": "No data received from the service"}, 500

        # Parse HTML to get download link
        soup = BeautifulSoup(response_json['data'], 'html.parser')
        download_btn = soup.select_one('.download-items__btn a')  # Update the selector if needed
        if not download_btn:
            logging.error("Download button not found")
            return {"error": "Download button not found"}, 500

        download_link = download_btn.get('href')
        if not download_link:
            logging.error("Download link not found")
            return {"error": "Download link not found"}, 500

        # Download the video
        video_response = requests.get(download_link, headers=headers, stream=True)
        if video_response.status_code != 200:
            logging.error(f"Failed to download video: {video_response.status_code}")
            return {"error": "Failed to download video"}, 500

        # Save the video
        filename = f"{reel_url.split('/')[-1]}.mp4"
        filepath = f"downloads/{filename}"
        with open(filepath, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Return the download URL
        return {
            "message": "Download successful",
            "download_url": f"/downloads/{filename}"
        }
    except RequestException as e:
        logging.error(f"Request failed: {e}")
        return {"error": str(e)}, 500
