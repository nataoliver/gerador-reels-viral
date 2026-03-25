import os
import random
import zipfile
import requests
import platform

from status import *
from config import *

DEFAULT_SONG_ARCHIVE_URLS = []


def close_running_selenium_instances() -> None:
    """
    Closes any running Selenium instances.

    Returns:
        None
    """
    try:
        info(" => Closing running Selenium instances...")

        # Kill all running Firefox instances
        if platform.system() == "Windows":
            os.system("taskkill /f /im firefox.exe")
        else:
            os.system("pkill firefox")

        success(" => Closed running Selenium instances.")

    except Exception as e:
        error(f"Error occurred while closing running Selenium instances: {str(e)}")


def build_url(youtube_video_id: str) -> str:
    """
    Builds the URL to the YouTube video.

    Args:
        youtube_video_id (str): The YouTube video ID.

    Returns:
        url (str): The URL to the YouTube video.
    """
    return f"https://www.youtube.com/watch?v={youtube_video_id}"


def rem_temp_files() -> None:
    """
    Removes temporary files in the `.mp` directory.

    Returns:
        None
    """
    # Path to the `.mp` directory
    mp_dir = os.path.join(ROOT_DIR, ".mp")

    files = os.listdir(mp_dir)

    for file in files:
        if not file.endswith(".json"):
            os.remove(os.path.join(mp_dir, file))


def fetch_songs() -> None:
    """
    Creates the Songs directory for generated videos.
    Remote zip download is disabled.

    Returns:
        None
    """
    try:
        info(f" => Checking Songs directory...")

        files_dir = os.path.join(ROOT_DIR, "Songs")
        if not os.path.exists(files_dir):
            os.mkdir(files_dir)
            if get_verbose():
                info(f" => Created directory: {files_dir}")
        else:
            if get_verbose():
                info(f" => Songs directory already exists.")

    except Exception as e:
        error(f"Error occurred while generating Songs directory: {str(e)}")


def choose_random_song() -> str:
    """
    Chooses a random song from the songs/ directory.

    Returns:
        str: The path to the chosen song.
    """
    try:
        songs_dir = os.path.join(ROOT_DIR, "Songs")
        songs = [
            name
            for name in os.listdir(songs_dir)
            if os.path.isfile(os.path.join(songs_dir, name))
            and name.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".ogg"))
        ]
        if len(songs) == 0:
            raise RuntimeError("No audio files found in Songs directory")
        song = random.choice(songs)
        success(f" => Chose song: {song}")
        return os.path.join(ROOT_DIR, "Songs", song)
    except Exception as e:
        error(f"Error occurred while choosing random song: {str(e)}")
        raise
