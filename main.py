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
SPOTIPY_CLIENT_ID = (
    os.environ["SPOTIPY_CLIENT_ID"] if "SPOTIPY_CLIENT_ID" in os.environ else None
)
SPOTIPY_CLIENT_SECRET = (
    os.environ["SPOTIPY_CLIENT_SECRET"]
    if "SPOTIPY_CLIENT_SECRET" in os.environ
    else None
)
SPOTIPY_REDIRECT_URI = (
    os.environ["SPOTIPY_REDIRECT_URI"] if "SPOTIPY_REDIRECT_URI" in os.environ else None
)
SPOTIPY_SCOPE = "playlist-read-private"

# Define YouTube API credentials and scope
YOUTUBE_TOKEN = os.environ["YOUTUBE_TOKEN"] if "YOUTUBE_TOKEN" in os.environ else None
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
    query = urllib.parse.quote(track)
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&q={query}&type=video&key={YOUTUBE_TOKEN}"
    sleep(1)
    response = requests.get(url)
    response_json = json.loads(response.text)
    if response.status_code not in [200, 201, 202, 203]:
        print(response_json["error"]["message"])
        exit(1)
    if len(response_json["items"]) > 0:
        return response_json["items"][0]["id"]["videoId"]

    return None


# Create YouTube playlist if one does not exist
def create_youtube_playlist(youtube, title, description):
    # Check if playlist already exists
    playlists_list_response = (
        youtube.playlists().list(part="snippet", mine=True).execute()
    )
    for playlist in playlists_list_response.get("items", []):
        if playlist["snippet"]["title"] == title:
            # Playlist with the same title already exists, return its ID
            return playlist["id"]

    # Playlist does not exist, create a new one
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


# Add YouTube video to playlist if it does not exist
def add_video_to_youtube_playlist(youtube, playlist_id, video_id):
    # Check if the video already exists in the playlist
    playlist_items = (
        youtube.playlistItems()
        .list(
            part="snippet",
            playlistId=playlist_id,
            videoId=video_id,
        )
        .execute()
    )

    if playlist_items["items"]:
        print("Video already exists in the playlist.")
        return True

    # Add the video to the playlist
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        },
    ).execute()

    return False


# Main function
def main():
    # s_list = [
    #     "https://open.spotify.com/playlist/464LdoI1kfhB1ZkhOW9sXp",
    #     "https://open.spotify.com/playlist/1pTd3EPhqc2aRSh4Ff2s6W",
    #     "https://open.spotify.com/playlist/3PaDY48jhuQPpmZyVMxbc1",
    #     "https://open.spotify.com/playlist/16scH7WG3T1PsWPdBYDjQ9",
    #     "https://open.spotify.com/playlist/532cjoCnqwpfhM0jCRuH9z",
    #     "https://open.spotify.com/playlist/0wAKVGP7KUgxtLQWDp8aHI",
    # ]

    # for spotify_playlist_url in s_list:
    #     # Get Spotify playlist URL from user input
    #     while True:
    #         if "open.spotify.com/playlist/" not in spotify_playlist_url:
    #             print("Invalid URL, please try again.")
    #         else:
    #             break

    #     # Extract playlist ID from URL
    #     playlist_id = spotify_playlist_url.split("/")[-1]

    #     # Get playlist title and description from Spotify API
    #     playlist = sp.playlist(playlist_id)
    #     playlist_title = playlist["name"]
    #     playlist_description = playlist["description"]

    #     # Convert and add tracks to YouTube playlist
    #     spotify_tracks = get_spotify_tracks(playlist_id)

    #     data = []
    #     for track in spotify_tracks:
    #         obj = {
    #             "sp_track_name": track["track"]["name"],
    #             "sp_track_artist": track["track"]["artists"][0]["name"],
    #         }
    #         data.append(obj)

    #     with open(f"Songs/{playlist_title}.json", "w+") as outfile:
    #         json.dump(data, outfile)

    #     print(f"Playlist conversion complete! : {playlist_title}")

    # Authenticate with YouTube API
    youtube = get_authenticated_service()

    playlist_titles = os.listdir("Songs")
    i = 0
    for playlist in playlist_titles:
        songs = None
        with open(f"Songs/{playlist}", "r") as playlist_file:
            # Create YouTube playlist
            playlist_name = playlist.replace(".json", "")
            youtube_playlist_id = create_youtube_playlist(
                youtube, playlist_name, f"This is a {playlist}"
            )
            songs = json.load(playlist_file)
            for song in songs:
                if "yt_video_id" in song and not song["yt_video_id"]:
                    continue
                name = song["sp_track_name"]
                artist = song["sp_track_artist"]
                if not name and not artist:
                    continue
                video_id, does_it_exist = convert_track_to_video(f"{name} + {artist}")
                if video_id:
                    add_video_to_youtube_playlist(
                        youtube, youtube_playlist_id, video_id
                    )
                    song["yt_video_id"] = video_id

        with open(f"Songs/{playlist}.json", "w+") as outfile:
            json.dump(songs, outfile)


if __name__ == "__main__":
    main()
