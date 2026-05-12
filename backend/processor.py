import json
import os
import subprocess
import shutil
import csv
import time
import uuid
from datetime import datetime

# search if the video exist, and call process
def search(filename, codec, fps):
    print("searching..."+ filename)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(current_dir, "source", "raw")
    target_file = os.path.join(raw_dir, f"{filename}.mp4")

    if os.path.exists(target_file):
        return process(filename, codec, fps)
    else:
        return None, f"File '{filename}.mp4' does not exist."

# generate log_id 
def create_log_id():
    time_part = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_part = uuid.uuid4().hex[:8]
    return f"{time_part}_{random_part}"

# save pending log
def save_pending_log(log_id, data):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(current_dir, "log", "pending")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{log_id}.json")

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# record video information
def get_video_info(video_file):
    try:
        duration_command = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_file
        ]

        duration_result = subprocess.run(
            duration_command,
            capture_output=True,
            text=True,
            check=True
        )

        video_length = round(float(duration_result.stdout.strip()), 3)

        resolution_command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            video_file
        ]

        resolution_result = subprocess.run(
            resolution_command,
            capture_output=True,
            text=True,
            check=True
        )

        resolution = resolution_result.stdout.strip()

        return video_length, resolution

    except Exception as e:
        print("GET VIDEO INFO ERROR:", str(e))
        return "", ""

# process video, use 2 helper method for easiler logic
def process(filename, codec, fps):
    log_id = create_log_id()
    print("processing"+ filename)

    # log start
    print("log_id:", log_id)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    raw_file = os.path.join(current_dir, "source", "raw", f"{filename}.mp4")

    video_length, resolution = get_video_info(raw_file)

    log_data = {
        "log_id": log_id,
        "video_name": filename,
        "codec": codec,
        "fps": fps,
        "video_length": video_length,
        "resolution": resolution,
        "is_cached": False,
        "encode_time": "",
        "slice_time": ""
    }

    encode_start = time.perf_counter() # log

    # encode start
    trans_file, is_cached, error = encode(filename, codec, fps)
    encode_end = time.perf_counter() # log
    if not trans_file:
        log_data["status"] = "encode_failed" # log
        log_data["error"] = error # log
        save_pending_log(log_id, log_data) # log
        return None, log_id, error
    
    log_data["is_cached"] = is_cached

    encode_time = round((encode_end - encode_start) * 1000, 3) # log
    log_data["encode_time"] = encode_time # log

    slice_start = time.perf_counter() # log
    manifest, error = dash(trans_file, codec)
    slice_end = time.perf_counter() # log
    slice_time = round((slice_end - slice_start) * 1000, 3) # log
    log_data["slice_time"] = slice_time # log
    if not manifest:
        log_data["status"] = "slice_failed" # log
        log_data["error"] = error # log
        save_pending_log(log_id, log_data) # log
        return None, log_id, error
    
    # log ends
    log_data["manifest"] = manifest
    log_data["status"] = "backend_finished"
    log_data["error"] = ""
    save_pending_log(log_id, log_data)

    return manifest, log_id, None

# encode video
def encode(filename, codec, fps):
    print("encoding" + filename)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(current_dir, "source", "raw")
    transcode_dir = os.path.join(current_dir, "source", "transcode")

    input_file = os.path.join(raw_dir, f"{filename}.mp4")

    if codec == "libvpx-vp9":
        output_file = os.path.join(transcode_dir, f"{filename}_{codec}_{fps}.webm")
    else:
        output_file = os.path.join(transcode_dir, f"{filename}_{codec}_{fps}.mp4")

    is_cached = False

    # a basic cache
    if os.path.exists(output_file):
        print("transcoded file already exists, reuse it")
        is_cached = True
        return output_file, is_cached, None
    
    os.makedirs(transcode_dir, exist_ok=True)

    case_commands = {
        ("libx264", "24"): [
            "ffmpeg", "-y",
            "-i", input_file,
            "-c:v", "libx264",
            "-r", "24",
            output_file
        ],
        ("libx264", "30"): [
            "ffmpeg", "-y",
            "-i", input_file,
            "-c:v", "libx264",
            "-r", "30",
            output_file
        ],
        ("libx264", "60"): [
            "ffmpeg", "-y",
            "-i", input_file,
            "-c:v", "libx264",
            "-r", "60",
            output_file
        ],
        ("libx265", "24"): [
            "ffmpeg", "-y",
            "-i", input_file,
            "-c:v", "libx265",
            "-r", "24",
            output_file
        ],
        ("libx265", "30"): [
            "ffmpeg", "-y",
            "-i", input_file,
            "-c:v", "libx265",
            "-r", "30",
            output_file
        ],
        ("libx265", "60"): [
            "ffmpeg", "-y",
            "-i", input_file,
            "-c:v", "libx265",
            "-r", "60",
            output_file
        ],
        ("libvpx-vp9", "24"): [
            "ffmpeg", "-y",
            "-i", input_file,
            "-c:v", "libvpx-vp9",
            "-b:v", "1M",
            "-r", "24",
            output_file
        ],
        ("libvpx-vp9", "30"): [
            "ffmpeg", "-y",
            "-i", input_file,
            "-c:v", "libvpx-vp9",
            "-b:v", "1M",
            "-r", "30",
            output_file
        ],
        ("libvpx-vp9", "60"): [
            "ffmpeg", "-y",
            "-i", input_file,
            "-c:v", "libvpx-vp9",
            "-b:v", "2M",
            "-r", "60",
            output_file
        ]
    }

    key = (codec, str(fps))
    if key not in case_commands:
        return None, is_cached, f"Unsupported codec/fps combination: codec={codec}, fps={fps}"

    command = case_commands[key]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return output_file, is_cached, None
    except subprocess.CalledProcessError as e:
        return None, is_cached, e.stderr
    except Exception as e:
        return None, is_cached, str(e)
    
# slice video for dash player
def dash(trans_file, codec):
    print("slicing " + trans_file)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    m4s_dir = os.path.join(current_dir, "source", "m4s")

    base_name = os.path.splitext(os.path.basename(trans_file))[0]
    output_dir = os.path.join(m4s_dir, base_name)

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    codec_lower = codec.lower().strip()

    # h.265 -> GPAC with mp4BOX
    if codec_lower in ["h.265", "hevc", "libx265"]:

        gpac_inputs = [
            trans_file + "#video"
        ]

        # if audio exist
        probe_command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=index",
            "-of", "csv=p=0",
            trans_file
        ]

        probe = subprocess.run(
            probe_command,
            capture_output=True,
            text=True
        )

        # if audio exists
        if probe.stdout.strip():
            print("audio track detected")
            gpac_inputs.append(trans_file + "#audio")
        else:
            print("no audio track")

        command = [
            "mp4box",
            "-dash", "2000",
            "-frag", "2000",
            "-rap",
            "-profile", "live",
            "-out", "manifest.mpd",
        ] + gpac_inputs

    # vp9 -> ffmpeg dash
    elif codec_lower in ["vp9", "libvpx-vp9"]:
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-i", trans_file,
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-c", "copy",
            "-f", "dash",
            "-seg_duration", "2",
            "-use_template", "1",
            "-use_timeline", "1",
            "-adaptation_sets", "id=0,streams=v id=1,streams=a",
            "-init_seg_name", "init-$RepresentationID$.webm",
            "-media_seg_name", "chunk-$RepresentationID$-$Number$.webm",
            "manifest.mpd"
        ]

    # default: h.264 -> ffmpeg
    else:
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-i", trans_file,
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-c", "copy",
            "-f", "dash",
            "-seg_duration", "2",
            "-use_template", "1",
            "-use_timeline", "1",
            "-adaptation_sets", "id=0,streams=v id=1,streams=a",
            "-streaming", "1",
            "-init_seg_name", "init-$RepresentationID$.m4s",
            "-media_seg_name", "chunk-$RepresentationID$-$Number$.m4s",
            "manifest.mpd"
        ]

    process = None

    try:
        print("COMMAND:", " ".join(command))

        process = subprocess.Popen(
            command,
            cwd=output_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        output_lines = []

        for line in process.stdout:
            print(line, end="")
            output_lines.append(line)

        process.wait()

        if process.returncode != 0:
            print("DASH ERROR START")
            print("".join(output_lines))
            print("DASH ERROR END")
            return None, "dash packaging failed, check server terminal"

        return f"{base_name}/manifest.mpd", None

    except FileNotFoundError as e:
        print("TOOL NOT FOUND:", str(e))
        return None, "required tool not found (ffmpeg or MP4Box)"

    except Exception as e:
        print("OTHER ERROR:", str(e))
        return None, str(e)

    finally:
        if process and process.stdout:
            process.stdout.close()

# log into file
def write_to_log(frontend_log):
    log_id = frontend_log.get("log_id")

    if not log_id:
        return False, "missing log_id"

    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(current_dir, "log")
    pending_dir = os.path.join(log_dir, "pending")

    pending_file = os.path.join(pending_dir, f"{log_id}.json")
    log_file = os.path.join(log_dir, "log.csv")

    if not os.path.exists(pending_file):
        return False, f"pending log not found for log_id: {log_id}"

    try:
        with open(pending_file, "r", encoding="utf-8") as f:
            backend_log = json.load(f)

        final_log = {
            "log_id": backend_log.get("log_id", log_id),
            "video_name": backend_log.get("video_name", ""),
            "codec": backend_log.get("codec", ""),
            "fps": backend_log.get("fps", ""),
            "video_length": backend_log.get("video_length", ""),
            "resolution": backend_log.get("resolution", ""),
            "is_cached": backend_log.get("is_cached", False),
            "start_up_delay": frontend_log.get("start_up_delay", ""),
            "encode_time": backend_log.get("encode_time", ""),
            "slice_time": backend_log.get("slice_time", ""),
            "avg_buffer_level": frontend_log.get("avg_buffer_level", ""),
            "avg_throughput_mbps": frontend_log.get("avg_throughput_mbps", ""),
            "drop_rate": frontend_log.get("drop_rate", ""),
            "decoded_frames": frontend_log.get("decoded_frames", ""),
            "dropped_frames": frontend_log.get("dropped_frames", ""),
            "status": backend_log.get("status", ""),
            "error": backend_log.get("error", "")
        }

        fieldnames = [
            "log_id",
            "video_name",
            "codec",
            "fps",
            "video_length",
            "resolution",
            "is_cached",
            "start_up_delay",
            "encode_time",
            "slice_time",
            "avg_buffer_level",
            "avg_throughput_mbps",
            "drop_rate",
            "decoded_frames",
            "dropped_frames",
            "status",
            "error"
        ]

        need_header = not os.path.exists(log_file) or os.path.getsize(log_file) == 0

        with open(log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if need_header:
                writer.writeheader()

            writer.writerow(final_log)

        os.remove(pending_file)
        
        return True, "frontend log saved"

    except Exception as e:
        print("WRITE TO LOG ERROR:", str(e))
        return False, str(e)
    
