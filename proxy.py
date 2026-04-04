from flask import Flask, request, jsonify
from flask_cors import CORS  # Import this
import os
import yt_dlp

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes automatically

@app.route("/")
def home():
    return "YouTube Music Proxy Running 🚀"

@app.route("/ping")
def ping():
    return "ok"

# ── 1. SEARCH API ──
@app.route("/search")
def search():
    import time

    q = request.args.get('q','')
    if not q:
        return jsonify([])

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "default_search": "ytsearch",
        "nocheckcertificate": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9"
        }
    }

    results = []

    try:
        time.sleep(0.3)  # anti-rate-limit

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            # 🔥 ORIGINAL SEARCH (KEEPED SAME)
            video_info = ydl.extract_info(f"ytsearch10:{q}", download=False)

            # 🔥 NEW: PLAYLIST SEARCH (ADDED)
            playlist_info = ydl.extract_info(f"ytsearch5:{q} playlist", download=False)

            # ── VIDEOS (same as before) ──
            if 'entries' in video_info:
                for entry in video_info['entries']:
                    if not entry:
                        continue

                    video_id = entry.get("id")
                    results.append({
                        "type": "video",
                        "title": entry.get("title"),
                        "videoId": video_id,
                        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                    })

            # ── PLAYLISTS (FINAL FIX) ──
if 'entries' in playlist_info:
    for entry in playlist_info['entries']:
        if not entry:
            continue

        pid = entry.get("id")

        # 🔥 FILTER REAL PLAYLIST IDS ONLY
        if not pid or not (pid.startswith("PL") or pid.startswith("UU") or pid.startswith("RD")):
            continue

        results.append({
            "type": "playlist",
            "title": entry.get("title"),
            "playlistId": pid,
            "thumbnail": entry.get("thumbnails", [{}])[-1].get("url", "")
        })

    except Exception as e:
        print(f"Search error: {e}")

    return jsonify(results)
    
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
        "playlistend": 40,
        "nocheckcertificate": True
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
        
    return jsonify(videos)

# ── 3. STREAM API ──
@app.route("/stream")
def stream():
    from datetime import datetime

    video_id = request.args.get("videoId")
    if not video_id:
        return jsonify({"error": "No videoId"}), 400

    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "bestaudio/best",
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "noplaylist": True,
        "extract_flat": False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # ── Get stream URL ──
            stream_url = info.get("url")

            if not stream_url and "formats" in info:
                audio_formats = [f for f in info["formats"] if f.get("acodec") != "none"]
                if audio_formats:
                    stream_url = audio_formats[-1]["url"]

            if not stream_url:
                return jsonify({"error": "Could not find stream"}), 404

            # ── Format upload date ──
            upload_date = info.get("upload_date")
            formatted_date = None

            if upload_date:
                try:
                    formatted_date = datetime.strptime(upload_date, "%Y%m%d").strftime("%d %b %Y")
                except:
                    formatted_date = upload_date  # fallback

            # ── Return full data ──
            return jsonify({
                "stream": stream_url,
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "uploadDate": formatted_date,
                "duration": info.get("duration"),
                "views": info.get("view_count"),
                "likeCount": info.get("like_count"),
                "thumbnail": info.get("thumbnail")
            })

    except Exception as e:
        print(f"CRITICAL: yt-dlp failed for {video_id}: {e}")
        return jsonify({
            "error": "YouTube blocked this request",
            "details": str(e)
        }), 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3001)))
