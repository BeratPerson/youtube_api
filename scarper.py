from flask import Flask, jsonify, request, Response
from flask_cors import CORS  # Import CORS
from youtubesearchpython import VideosSearch
import youtube_dl
import os
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def sanitize_filename(filename):
    # Remove invalid characters
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def search_youtube(query):
    videos_search = VideosSearch(query, limit=10)  # Get the first 10 results
    results = videos_search.result()['result']

    video_list = []

    for video in results:
        video_info = {
            'title': video['title'],
            'thumbnail': video['thumbnails'][0]['url'],  # Get the first thumbnail
            'channel': video['channel']['name'],
            'url': f"https://www.youtube.com/watch?v={video['id']}"  # Add video URL
        }
        video_list.append(video_info)

    return video_list

@app.route('/api/search', methods=['GET'])
def api_search():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Please specify a search query.'}), 400

    try:
        search_results = search_youtube(query)
        return jsonify(search_results)
    except Exception as e:
        return jsonify({'error': f'An error occurred during search: {str(e)}'}), 500

@app.route('/api/download', methods=['POST'])
def download_audio():
    data = request.json
    video_url = data.get('video_url')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloaded_audio.%(ext)s',
        'keepvideo': True,
        'prefer_ffmpeg': False,
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            audio_file_path = ydl.prepare_filename(info_dict).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            video_file_path = ydl.prepare_filename(info_dict)

        # Check if the audio file exists, otherwise use the video file
        if os.path.exists(audio_file_path):
            file_path = audio_file_path
            mimetype = 'audio/mp3'
        else:
            file_path = video_file_path
            mimetype = 'video/webm'

        # Read the file
        with open(file_path, 'rb') as f:
            file_data = f.read()

        os.remove(file_path)  # Clean up by removing the file

        return Response(file_data, mimetype=mimetype, headers={'Content-Disposition': f'attachment;filename={info_dict.get("title", "audio")}.mp3'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
