from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

YOUTUBE_API = "https://www.youtube.com/youtubei/v1/search?prettyPrint=false"

@app.route("/")
def home():
    return "YouTube Proxy Running 🚀"

@app.route("/ping")
def ping():
    return "ok"

@app.route("/search")
def search():
    q = request.args.get("q", "")

    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20231121.08.00"
            }
        },
        "query": q
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.post(YOUTUBE_API, json=payload, headers=headers)
        data = r.json()

        resp = jsonify(data)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3001)))
