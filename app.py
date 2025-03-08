# app.py (Backend - Flask)
from flask import Flask, render_template, request
import instaloader
from urllib.parse import urlparse

app = Flask(__name__)

def is_instagram_url(url):
    parsed = urlparse(url)
    return parsed.netloc in ['www.instagram.com', 'instagram.com']

def get_shortcode_from_url(url):
    path = urlparse(url).path.strip('/')
    parts = path.split('/')
    if len(parts) >= 2 and parts[0] in ['p', 'reel', 'tv']:
        return parts[1]
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    media_urls = []
    
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        
        if not url:
            error = "Please enter a URL"
        elif not is_instagram_url(url):
            error = "Invalid Instagram URL"
        else:
            shortcode = get_shortcode_from_url(url)
            if not shortcode:
                error = "Could not extract post ID from URL"
            else:
                try:
                    L = instaloader.Instaloader()
                    post = instaloader.Post.from_shortcode(L.context, shortcode)
                    
                    if post.typename == 'GraphImage':
                        media_urls.append(post.url)
                    elif post.typename == 'GraphVideo':
                        media_urls.append(post.video_url)
                    elif post.typename == 'GraphSidecar':
                        for node in post.get_sidecar_nodes():
                            if node.is_video:
                                media_urls.append(node.video_url)
                            else:
                                media_urls.append(node.display_url)
                    else:
                        error = "Unsupported post type"
                except Exception as e:
                    error = f"Error fetching post: {str(e)}"

    return render_template('index.html', error=error, media_urls=media_urls)

if __name__ == '__main__':
    app.run(debug=True)
