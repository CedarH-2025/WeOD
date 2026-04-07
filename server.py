from flask import Flask, request, jsonify, send_from_directory
from backend.processor import search
app = Flask(__name__)

# define api
@app.route('/api/start', methods=['POST'])
def handle_start():
    data = request.json
    video_name = data.get('title')
    
    # search from backend
    manifest, status = search(video_name)
    
    if manifest:
        return jsonify({
            "message": "Success, starting to play",
            "url": f"/stream/{video_name}_temp/playlist.mpd"
        }), 200
    else:
        return jsonify({"error": status}), 404

# flask send m4s
@app.route('/stream/<path:filename>')
def serve_video(filename):
    return send_from_directory('backend/source/m4s', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)