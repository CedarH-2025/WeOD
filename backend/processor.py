import os
import subprocess
import shutil

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

#process video, use 2 helper method for easiler logic
def process(filename, codec, fps):
    print("processing"+ filename)
    trans_file, error = encode(filename, codec, fps)
    if not trans_file:
        return None, error

    manifest, error = dash(trans_file, codec)
    if not manifest:
        return None, error

    return manifest, None

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

    # a basic cache
    if os.path.exists(output_file):
        print("transcoded file already exists, reuse it")
        return output_file, None
    
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
        return None, f"Unsupported codec/fps combination: codec={codec}, fps={fps}"

    command = case_commands[key]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return output_file, None
    except subprocess.CalledProcessError as e:
        return None, e.stderr
    except Exception as e:
        return None, str(e)
    
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

    # h.265 -> GPAC
    if codec_lower in ["h.265", "hevc", "libx265"]:
        command = [
            "mp4box",
            "-dash", "2000",
            "-frag", "2000",
            "-rap",
            "-profile", "live",
            "-out", "manifest.mpd",
            trans_file + "#video",
            trans_file + "#audio"
        ]

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
    
