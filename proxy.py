from flask import Flask, request, jsonify
import requests
import os
import yt_dlp

app = Flask(__name__)

@app.route("/")
def home():
    return "YouTube Music Proxy Running 🚀"

@app.route("/ping")
def ping():
    return "ok"

# ── 1. SEARCH API (Optimized for Speed) ──
@app.route("/search")
def search():
    q = request.args.get('q','')
    if not q:
        return jsonify([])

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "force_generic_extractor": False,
        "default_search": "ytsearch10",
    }

    videos = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # We search directly via yt-dlp to avoid manually parsing complex JSON
            info = ydl.extract_info(f"ytsearch10:{q}", download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        videos.append({
                            "title": entry.get("title"),
                            "videoId": entry.get("id"),
                            "thumbnail": f"https://i.ytimg.com/vi/{entry.get('id')}/hqdefault.jpg"
                        })
    except Exception as e:
        print(f"Search error: {e}")

    resp = jsonify(videos)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

# ── 2. PLAYLIST API ──
@app.route("/playlist")
def playlist():
    playlist_id = request.args.get('id', '')
    if not playlist_id:
        return jsonify([])

    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    ydl_opts = {
        "quiet": True,
        "extract_flat": True, 
        "skip_download": True,
        "playlistend": 40 
    }

    videos = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    title = entry.get('title', '')
                    video_id = entry.get('id')
                    if not video_id or not title or title.lower() in ['[private video]', '[deleted video]']:
                        continue
                    
                    videos.append({
                        "title": title,
                        "videoId": video_id,
                        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                    })
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        
    resp = jsonify(videos)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

# ── 3. STREAM API (Fixed with Safety Net) ──
@app.route("/stream")
def stream():
    video_id = request.args.get("videoId")
    if not video_id:
        return jsonify({"error": "No videoId"}), 400

    url = f"https://www.youtube.com/watch?v={video_id}"

    # Adding a real User-Agent helps slightly with the bot detection
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "bestaudio/best",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info.get("url")
            
            if not stream_url:
                return jsonify({"error": "Could not find stream"}), 404

            resp = jsonify({"stream": stream_url})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

    except Exception as e:
        print(f"CRITICAL: yt-dlp failed for {video_id}: {e}")
        # Return a 403 (Forbidden) instead of crashing with a 500
        resp = jsonify({"error": "YouTube blocked this request", "details": str(e)})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp, 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3001)))
