# WeOD
VOD system for cs537 Final Project
Designed for windows

This is a server-cilent mode VOD System. 

# install:
1. winget install ffmpeg
2. winget install gpac

# running:
In the root folder of this software, run: python server.py


# reference:
browser supported codecs:
https://www.reddit.com/r/MicrosoftEdge/comments/v9iw8k/enable_hevc_support_in_edge/
https://learn.microsoft.com/en-us/troubleshoot/microsoft-edge/development/video-playback-issues
https://vdo.ninja/h265
Chrome native support hevc. Edge doesn't. So the hevc test is through chrome. hevc is common but not widely supported. This is mainly because of the lisences problem. 

dash.js does not natively support MJPEG streams — it is designed for MPEG-DASH (ISO/IEC 23009-1) adaptive bitrate video, not raw MJPEG HTTP streams. MJPEG is a frame-by-frame video format typically delivered via HTTP with a .mjpg or .jpg extension, while MPEG-DASH uses an MPD (Media Presentation Description) manifest to describe segmented video/audio content.

dash.js: is a JavaScript-based MPEG-DASH reference player developed by the DASH Industry Forum. It uses the HTML5 \<video\> element with MSE to load and play adaptive bitrate video segments from an MPD manifest. It can also integrate with DRM systems via EME for encrypted content.
Which mean dash.js is based on MSE(Media Source Extensions), and MJPEG is a type of different streaming format with MSE, thus MJEPG is not support on DASH.js
https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Video_codecs
https://github.com/blakeblackshear/frigate/discussions/18634
https://www.rfc-editor.org/rfc/rfc6381#section-3.4
https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Video_codecs

console.log("MP4 MJPEG:", MediaSource.isTypeSupported('video/mp4; codecs="mjp2"'));
VM71:1 MP4 MJPEG: false

# Data Collection
I use Videos from Xiph.org Video Test Media [derf's collection]. 

Videos are from https://media.xiph.org/







