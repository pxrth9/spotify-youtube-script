from time import sleep
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
import json
import urllib.parse
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Define Spotify API credentials and scope
SPOTIPY_CLIENT_ID = os.environ['SPOTIPY_CLIENT_ID']
SPOTIPY_CLIENT_SECRET = os.environ['SPOTIPY_CLIENT_SECRET']
SPOTIPY_REDIRECT_URI = os.environ['SPOTIPY_REDIRECT_URI']
SPOTIPY_SCOPE = "playlist-read-private"

# Define YouTube API credentials and scope
YOUTUBE_TOKEN = os.environ['YOUTUBE_TOKEN']
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# Authenticate with Spotify API
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SPOTIPY_SCOPE,
    )
)


# Authenticate with YouTube API
def get_authenticated_service():
    # Load client secrets from a local file.
    flow = InstalledAppFlow.from_client_secrets_file("youtube_cred.json", scopes=SCOPES)

    # Try to load existing credentials from the authorized user file.
    creds = None
    try:
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    except FileNotFoundError:
        pass

    # If the existing credentials are invalid or don't exist, run the flow to get new credentials.
    if not creds or not creds.valid:
        creds = flow.run_local_server(port=8080)

    # Save the credentials for the next run.
    with open("token.json", "w") as token:
        token.write(creds.to_json())

    # Return an authenticated instance of the YouTube API client.
    return build("youtube", "v3", credentials=creds)


# Get Spotify playlist tracks
def get_spotify_tracks(playlist_id):
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    tracks.extend(results["items"])
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])
    return tracks


# Convert Spotify track to YouTube video ID
def convert_track_to_video(track):
    query = track["track"]["name"] + " " + track["track"]["artists"][0]["name"]
    query = urllib.parse.quote(query)
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&q={query}&type=video&key="
    print({query: url})
    sleep(1)
    response = requests.get(url)
    response_json = json.loads(response.text)
    if len(response_json["items"]) > 0:
        return response_json["items"][0]["id"]["videoId"]
    else:
        return None


# Create YouTube playlist
def create_youtube_playlist(youtube, title, description):
    playlists_insert_response = (
        youtube.playlists()
        .insert(
            part="snippet,status",
            body=dict(
                snippet=dict(title=title, description=description),
                status=dict(privacyStatus="private"),
            ),
        )
        .execute()
    )
    return playlists_insert_response["id"]


# Add YouTube video to playlist
def add_video_to_youtube_playlist(youtube, playlist_id, video_id):
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        },
    ).execute()


# Main function
def main():
    print("Main Function")
    s_list = [
        "https://open.spotify.com/playlist/464LdoI1kfhB1ZkhOW9sXp",
        "https://open.spotify.com/playlist/1pTd3EPhqc2aRSh4Ff2s6W",
        "https://open.spotify.com/playlist/3PaDY48jhuQPpmZyVMxbc1",
        "https://open.spotify.com/playlist/16scH7WG3T1PsWPdBYDjQ9",
        "https://open.spotify.com/playlist/532cjoCnqwpfhM0jCRuH9z",
        "https://open.spotify.com/playlist/0wAKVGP7KUgxtLQWDp8aHI",
    ]
    for spotify_playlist_url in s_list:
        # Get Spotify playlist URL from user input
        while True:
            if "open.spotify.com/playlist/" not in spotify_playlist_url:
                print("Invalid URL, please try again.")
            else:
                break

        # Extract playlist ID from URL
        playlist_id = spotify_playlist_url.split("/")[-1]

        # Get playlist title and description from Spotify API
        playlist = sp.playlist(playlist_id)
        playlist_title = playlist["name"]
        playlist_description = playlist["description"]

        # Authenticate with YouTube API
        # youtube = get_authenticated_service()

        # Create YouTube playlist
        # youtube_playlist_id = create_youtube_playlist(
        #     youtube, playlist_title, playlist_description
        # )

        # Convert and add tracks to YouTube playlist
        spotify_tracks = get_spotify_tracks(playlist_id)

        data = []
        for track in spotify_tracks:
            track_name = track["track"]["name"]
            track_artist = track["track"]["artists"][0]["name"]
            data.append({f"{track_name}": f"{track_artist}"})

        with open(f"Songs/{playlist_title}.json", "w") as outfile:
            json.dump(data, outfile)

        print(f"Playlist conversion complete! : {playlist_title}")


if __name__ == "__main__":
    main()
