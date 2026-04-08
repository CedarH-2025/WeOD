from flask import Flask, request, jsonify, send_from_directory
from backend.processor import search
app = Flask(__name__)

# index
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

# define api
@app.route('/api/start', methods=['POST'])
def handle_start():
    data = request.json
    video_name = data.get('title')
    codec = data.get('codec')
    fps = data.get('fps')
    
    # search from backend
    manifest, status = search(video_name, codec, fps)
    
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

# In Debug Mode
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)