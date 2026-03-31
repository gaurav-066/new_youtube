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

# ── 1. SEARCH API ──
@app.route("/search")
def search():
    q = request.args.get('q','')

    r = requests.post(
        'https://www.youtube.com/youtubei/v1/search?prettyPrint=false',
        json={
            "context":{
                "client":{
                    "clientName":"WEB",
                    "clientVersion":"2.20231121.08.00"
                }
            },
            "query":q
        },
        headers={"User-Agent":"Mozilla/5.0"}
    )

    data = r.json()
    videos = []

    contents = (
        data.get('contents', {})
        .get('twoColumnSearchResultsRenderer', {})
        .get('primaryContents', {})
        .get('sectionListRenderer', {})
        .get('contents', [])
    )

    for section in contents:
        items = section.get('itemSectionRenderer', {}).get('contents', [])

        for item in items:
            video = item.get('videoRenderer')

            if not video:
                continue

            video_id = video.get('videoId')

            title = (
                video.get('title', {})
                .get('runs', [{}])[0]
                .get('text', '')
            )

            thumbnail = (
                video.get('thumbnail', {})
                .get('thumbnails', [{}])[-1]
                .get('url', '')
            )

            if video_id:
                videos.append({
                    "title": title,
                    "videoId": video_id,
                    "thumbnail": thumbnail
                })

    resp = jsonify(videos)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


# ── 2. PLAYLIST API (Now filters out Private/Deleted videos!) ──
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

                    # 1. Skip if there's no ID or Title at all
                    if not video_id or not title:
                        continue
                    
                    # 2. Skip YouTube's ghost placeholders
                    if title.lower() in ['[private video]', '[deleted video]']:
                        continue

                    # Get the best thumbnail available
                    thumbnails = entry.get('thumbnails', [])
                    thumb_url = thumbnails[-1]['url'] if thumbnails else ''
                    
                    videos.append({
                        "title": title,
                        "videoId": video_id,
                        "thumbnail": thumb_url
                    })
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        
    resp = jsonify(videos)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


# ── 3. STREAM API ──
@app.route("/stream")
def stream():
    video_id = request.args.get("videoId")

    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "bestaudio/best"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        stream_url = info["url"]

    resp = jsonify({
        "stream": stream_url
    })
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3001)))
