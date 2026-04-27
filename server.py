from flask import Flask, request, jsonify, send_from_directory
from backend.processor import search, write_to_log
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
    manifest, log_id, status = search(video_name, codec, fps)
    
    if manifest:
        return jsonify({
            "message": "Success, starting to play",
            "url": f"/stream/{manifest}",
            "log_id": log_id
        }), 200
    else:
        return jsonify({"error": status}), 404

# flask send m4s
@app.route('/stream/<path:filename>')
def serve_video(filename):
    return send_from_directory('backend/source/m4s', filename)

# log from front-end
@app.route('/api/log_frontend', methods=['POST'])
def log_frontend():
    data = request.json
    success, message = write_to_log(data)

    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400

# In Debug Mode
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

    