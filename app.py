import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urlparse

def get_instagram_media(url):
    # Rotating headers and delays to avoid detection
    headers_list = [
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.5",
        },
        {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15",
            "Accept-Language": "en-US,en;q=0.9",
        },
    ]

    try:
        # Validate URL
        parsed = urlparse(url)
        if not parsed.netloc in ['www.instagram.com', 'instagram.com']:
            return {"error": "Invalid Instagram URL"}

        # Add random delay
        time.sleep(random.uniform(1, 3))

        # Make request with random headers
        response = requests.get(
            url,
            headers=random.choice(headers_list),
            timeout=10
        )

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', text=re.compile('window\.__additionalDataLoaded'))
            
            if script_tag:
                # Extract JSON data
                json_data = re.search(r'({.*});</script>', script_tag.string).group(1)
                media_url = re.search(r'"video_url":"(https:\\/\\/.*?)"', json_data)
                
                if media_url:
                    return {
                        "url": media_url.group(1).replace('\\/', '/'),
                        "type": "video"
                    }
                else:
                    return {"error": "No video found in post"}
            
        elif response.status_code == 429:
            return {"error": "Rate limited - try again later"}
            
        return {"error": "Content not found"}

    except Exception as e:
        return {"error": str(e)}

# Example usage
result = get_instagram_media("https://www.instagram.com/p/C_vJXR1yWZP/")
print(result)
