# Spotify to YouTube Playlist Converter

This script allows you to convert a Spotify playlist to a YouTube playlist.

## Setup

1. Clone the repository:

   ```
   git clone https://github.com/your_username/spotify-to-youtube-playlist-converter.git
   cd spotify-to-youtube-playlist-converter
   ```
2. Create and activate a new virtual environment:

   ```
   python3 -m venv venv
   source venv/bin/activate   # for Linux/macOS
   venv\Scripts\activate.bat  # for Windows
   ```
3. Install the required packages:

   ```python
   pip install -r requirements.txt
   ```

## Usage

1. Authenticate with the Spotify API by setting the following environment variables:

   ```
   export SPOTIPY_CLIENT_ID=
   export SPOTIPY_CLIENT_SECRET=
   export SPOTIPY_REDIRECT_URI=http://localhost:8000/callback
   export YOUTUBE_TOKEN=
   ```
2. Authenticate with the YouTube API by following the instructions in the script.
3. Run the script:

   ```
   python3 main.py
   ```
4. Enter the Spotify playlist URL when prompted.
5. Wait for the script to convert the playlist and add the tracks to a new YouTube playlist.
6. Deactivate the virtual environment:

   ```
   deactivate
   ```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
