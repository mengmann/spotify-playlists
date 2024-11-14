#!/usr/bin/env python3

# Copyright (C) 2017 Felix Geyer <debfx@fobos.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 or (at your option)
# version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import configparser
import os
import xml.etree.ElementTree
import logging
import glob

import jinja2
import spotipy
import spotipy.cache_handler
import spotipy.oauth2
import spotipy.util

import constants

# Configure the logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def delete_all_user_playlists(sp):
    # Get the current user’s ID
    user_id = sp.current_user()["id"]

    # Start fetching playlists with pagination
    playlists = sp.current_user_playlists(limit=50)

    confirmation = input(
        f"Do you really want to delete all playlists from account '{user_id}'? (yes/no): "
    )

    # Loop through playlists and ask for confirmation before deletion
    while playlists:
        for playlist in playlists["items"]:
            if (
                playlist["owner"]["id"] == user_id
            ):  # Check if the user owns the playlist
                if confirmation.lower() == "yes":
                    sp.current_user_unfollow_playlist(playlist["id"])
                    logger.info("Deleted playlist: %s", playlist["name"])
                else:
                    logger.info("Skipped deletion of playlist: %s", playlist["name"])

        # Continue to the next page of playlists
        playlists = sp.next(playlists) if playlists["next"] else None


def delete_all_saved_tracks(sp):
    """Retrieve all saved tracks for the user and delete them after confirmation."""

    # Fetch all saved tracks with pagination
    saved_tracks = sp.current_user_saved_tracks(limit=50)
    all_track_ids = [item["track"]["id"] for item in saved_tracks["items"]]

    while saved_tracks["next"]:
        saved_tracks = sp.next(saved_tracks)
        all_track_ids.extend(item["track"]["id"] for item in saved_tracks["items"])

    if not all_track_ids:
        logger.info("No saved tracks found.")
        return

    # Confirm deletion with the user
    confirmation = input(
        f"You have {len(all_track_ids)} saved tracks. Do you want to delete them all? (yes/no): "
    )
    if confirmation.lower() != "yes":
        logger.info("Operation cancelled. No tracks were deleted.")
        return

    # Delete tracks in chunks of 50 (Spotify API limit)
    for i in range(0, len(all_track_ids), 50):
        chunk = all_track_ids[i : i + 50]
        sp.current_user_saved_tracks_delete(tracks=chunk)
        logger.info("Deleted %d tracks from saved tracks.", len(chunk))

    logger.info("All saved tracks have been deleted.")


def delete_all_saved_albums(sp):
    """Retrieve all saved albums for the user and delete them after confirmation."""

    # Fetch all saved albums with pagination
    saved_albums = sp.current_user_saved_albums(limit=50)
    all_album_ids = [item["album"]["id"] for item in saved_albums["items"]]

    while saved_albums["next"]:
        saved_albums = sp.next(saved_albums)
        all_album_ids.extend(item["album"]["id"] for item in saved_albums["items"])

    if not all_album_ids:
        logger.info("No saved albums found.")
        return

    # Confirm deletion with the user
    confirmation = input(
        f"You have {len(all_album_ids)} saved albums. Do you want to delete them all? (yes/no): "
    )
    if confirmation.lower() != "yes":
        logger.info("Operation cancelled. No albums were deleted.")
        return

    # Delete albums in chunks of 50 (Spotify API limit)
    for i in range(0, len(all_album_ids), 50):
        chunk = all_album_ids[i : i + 50]
        sp.current_user_saved_albums_delete(albums=chunk)
        logger.info("Deleted %d albums from saved albums.", len(chunk))

    logger.info("All saved albums have been deleted.")


def delete_all_saved_shows(sp):
    """Retrieve all saved shows for the user and delete them after confirmation."""

    # Fetch all saved shows with pagination
    saved_shows = sp.current_user_saved_shows(limit=50)
    all_show_ids = [item["show"]["id"] for item in saved_shows["items"]]

    while saved_shows["next"]:
        saved_shows = sp.next(saved_shows)
        all_show_ids.extend(item["show"]["id"] for item in saved_shows["items"])

    if not all_show_ids:
        logger.info("No saved shows found.")
        return

    # Confirm deletion with the user
    confirmation = input(
        f"You have {len(all_show_ids)} saved shows. Do you want to delete them all? (yes/no): "
    )
    if confirmation.lower() != "yes":
        logger.info("Operation cancelled. No shows were deleted.")
        return

    # Delete shows in chunks of 50 (Spotify API limit)
    for i in range(0, len(all_show_ids), 50):
        chunk = all_show_ids[i : i + 50]
        sp.current_user_saved_shows_delete(shows=chunk)
        logger.info("Deleted %d shows from saved shows.", len(chunk))

    logger.info("All saved shows have been deleted.")


def process_tracks(tracks):
    result = []

    for item in tracks["items"]:
        track = item["track"]

        if track is None:
            # some playlists have extra "null" tracks (without any information), just skip them
            continue
        if track.get("uri", str()).startswith("spotify:local"):
            # local files are not supported
            continue
        artists = ";".join([artist["name"] for artist in track["artists"]])
        result.append({"title": track["name"], "artists": artists, "uri": track["uri"]})

    return result


def process_albums(albums):
    result = []

    for item in albums["items"]:
        album = item["album"]

        artists = ";".join([artist["name"] for artist in album["artists"]])
        result.append({"title": album["name"], "artists": artists, "uri": album["uri"]})

    return result


def process_shows(shows):
    result = []

    for item in shows["items"]:
        show = item["show"]
        result.append(
            {"title": show["name"], "artists": show["publisher"], "uri": show["uri"]}
        )

    return result


def write_playlist(
    name, dirname, tracks, pl_type, location=None, public=False, collaborative=False
):
    env = jinja2.Environment(autoescape=True)
    template = env.from_string(constants.PLAYLIST_TEMPLATE)
    content = template.render(
        title=name,
        location=location,
        tracklist=tracks,
        pl_type=pl_type,
        public=public,
        collaborative=collaborative,
    )

    if pl_type == "saved_tracks":
        xspf_path = f"{dirname}/{constants.FILEPATH_SAVED_TRACKS}"
    else:
        xspf_path = f"{dirname}/{name.replace('/', '_')}.xspf"

    with open(xspf_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info('saved playlist "%s" to "%s"', name, xspf_path)


def write_albums(dirname, albums):
    env = jinja2.Environment(autoescape=True)
    template = env.from_string(constants.ALBUM_TEMPLATE)
    content = template.render(
        albumlist=albums,
    )

    xspf_path = f"{dirname}/{constants.FILEPATH_SAVED_ALBUMS}"

    with open(xspf_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info('saved albums to "%s"', xspf_path)


def write_shows(dirname, shows):
    env = jinja2.Environment(autoescape=True)
    template = env.from_string(constants.SHOW_TEMPLATE)
    content = template.render(
        showlist=shows,
    )

    xspf_path = f"{dirname}/{constants.FILEPATH_SAVED_SHOWS}"

    with open(xspf_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info('saved shows to "%s"', xspf_path)


def export_playlists(sp, username, dirname):
    if not os.path.isdir(dirname):
        os.mkdir(dirname)

    playlists = sp.user_playlists(username, limit=50, offset=0)
    playlist_items = playlists["items"]
    while playlists["next"]:
        playlists = sp.next(playlists)
        playlist_items.extend(playlists["items"])

    for playlist in playlist_items:
        tracks = sp.playlist_items(
            playlist["id"],
            fields="items(track(name,artists(name),uri)),next",
        )
        tracks_processed = process_tracks(tracks)
        while tracks["next"]:
            tracks = sp.next(tracks)
            tracks_processed.extend(process_tracks(tracks))
        write_playlist(
            playlist["name"],
            dirname,
            tracks_processed,
            pl_type="playlist",
            location=playlist["uri"],
            public=playlist["public"],
            collaborative=playlist["collaborative"],
        )

    tracks = sp.current_user_saved_tracks()
    tracks_processed = process_tracks(tracks)
    while tracks["next"]:
        tracks = sp.next(tracks)
        tracks_processed.extend(process_tracks(tracks))
    write_playlist("Saved tracks", dirname, tracks_processed, pl_type="saved_tracks")


def export_albums(sp, filename):
    saved_albums = sp.current_user_saved_albums(limit=50)
    albums_processed = process_albums(saved_albums)

    # Use pagination to fetch all saved albums
    while saved_albums["next"]:
        saved_albums = sp.next(saved_albums)
        albums_processed.extend(process_albums(saved_albums))

    write_albums(
        filename,
        albums_processed,
    )


def export_shows(sp, filename):
    saved_shows = sp.current_user_saved_shows(limit=50)
    shows_processed = process_shows(saved_shows)

    # Use pagination to fetch all saved shows
    while saved_shows["next"]:
        saved_shows = sp.next(saved_shows)
        shows_processed.extend(process_shows(saved_shows))

    write_shows(
        filename,
        shows_processed,
    )


def _get_existing_playlist_id(sp, username, playlist_name):
    """Return the ID of an existing playlist with the given name, or None if it doesn't exist."""
    playlists = sp.user_playlists(username)
    playlist_items = playlists["items"]

    # Use Spotipy's built-in paginator to fetch all playlists
    while playlists["next"]:
        playlists = sp.next(playlists)
        playlist_items.extend(playlists["items"])

    # Search for a playlist with the given name
    for playlist in playlist_items:
        if playlist["name"] == playlist_name:
            return playlist["id"]

    return None


def _get_playlist_track_uris(sp, playlist_id):
    """Retrieve all track URIs currently in the specified playlist."""
    track_uris = set()
    results = sp.playlist_tracks(playlist_id)
    while results:
        for item in results["items"]:
            track_uris.add(item["track"]["uri"])
        results = sp.next(results) if results["next"] else None
    return track_uris


def import_playlist(sp, username, filename):
    def _import_playlist_from_file(sp, username, filename):
        tree = xml.etree.ElementTree.parse(filename)
        root = tree.getroot()

        name = root.find("{http://xspf.org/ns/0/}title").text
        tracks = []
        public = False
        collaborative = False

        for elem in root.findall(
            "{http://xspf.org/ns/0/}trackList/{http://xspf.org/ns/0/}track"
        ):
            location = elem.find("{http://xspf.org/ns/0/}location").text
            tracks.append(location)

        elem_extension = root.find(
            "{http://xspf.org/ns/0/}extension[@application='https://github.com/debfx/spotify-playlists']"
        )
        if elem_extension is not None:
            elem_public = elem_extension.find("{http://xspf.org/ns/0/}public")
            if elem_public is not None:
                public = elem_public.text.lower() == "true"

            elem_collaborative = elem_extension.find(
                "{http://xspf.org/ns/0/}collaborative"
            )
            if elem_collaborative is not None:
                collaborative = elem_collaborative.text.lower() == "true"

        # Check for an existing playlist with the same name
        playlist_id = _get_existing_playlist_id(sp, username, name)
        if playlist_id is None:
            # Create a new playlist if no existing playlist is found
            playlist_id = sp.user_playlist_create(username, name, public=public)["id"]
            logger.info('Created new playlist "%s"', name)
        else:
            logger.info('Using existing playlist "%s"', name)

        # Set collaborative setting if needed
        if collaborative:
            sp.user_playlist_change_details(
                username, playlist_id, collaborative=collaborative
            )

        # Get current track URIs in the playlist
        existing_track_uris = _get_playlist_track_uris(sp, playlist_id)

        # Filter tracks to add only new ones
        new_tracks = [track for track in tracks if track not in existing_track_uris]

        if len(new_tracks) > 0:
            # Add new tracks in chunks of 100 (Spotify API limit)
            for tracks_chunk in chunks(new_tracks, 100):
                sp.user_playlist_add_tracks(username, playlist_id, tracks_chunk)
                logger.info(
                    'Added %d new tracks to playlist "%s"', len(tracks_chunk), name
                )
        else:
            logger.info('Added %d new tracks to playlist "%s"', 0, name)

        logger.info('Imported playlist "%s" from "%s"', name, filename)

    # Process all .xspf files in the given directory or file
    if os.path.isdir(filename):
        # Iterate over all .xspf files in the directory
        for file_path in glob.glob(os.path.join(filename, "*.xspf")):
            # these are handled separately. skip them
            if os.path.basename(file_path) in [
                constants.FILEPATH_SAVED_TRACKS,
                constants.FILEPATH_SAVED_SHOWS,
                constants.FILEPATH_SAVED_ALBUMS,
            ]:
                continue
            _import_playlist_from_file(sp, username, file_path)
    elif os.path.isfile(filename) and filename.endswith(".xspf"):
        # If filename is a single .xspf file, process it directly
        _import_playlist_from_file(sp, username, filename)
    else:
        logger.error("The provided filename is neither a directory nor a .xspf file.")


def import_saved_tracks(sp, filename):
    tree = xml.etree.ElementTree.parse(f"{filename}/{constants.FILEPATH_SAVED_TRACKS}")
    root = tree.getroot()

    tracks = []

    for elem in root.findall(
        "{http://xspf.org/ns/0/}trackList/{http://xspf.org/ns/0/}track"
    ):
        location = elem.find("{http://xspf.org/ns/0/}location").text
        tracks.append(location)

    for tracks_chunk in chunks(tracks, 50):
        sp.current_user_saved_tracks_add(tracks=tracks_chunk)
        logger.info("Added %d new tracks to saved tracks", len(tracks_chunk))


def import_albums(sp, filename):
    tree = xml.etree.ElementTree.parse(f"{filename}/{constants.FILEPATH_SAVED_ALBUMS}")
    root = tree.getroot()

    albums = []

    for elem in root.findall(
        "{http://xspf.org/ns/0/}albumList/{http://xspf.org/ns/0/}album"
    ):
        location = elem.find("{http://xspf.org/ns/0/}location").text
        albums.append(location)

    for albums_chunk in chunks(albums, 50):
        sp.current_user_saved_albums_add(albums=albums_chunk)
        logger.info("Added %d new tracks to saved albums", len(albums_chunk))


def import_shows(sp, filename):
    tree = xml.etree.ElementTree.parse(f"{filename}/{constants.FILEPATH_SAVED_SHOWS}")
    root = tree.getroot()

    shows = []

    for elem in root.findall(
        "{http://xspf.org/ns/0/}showList/{http://xspf.org/ns/0/}show"
    ):
        location = elem.find("{http://xspf.org/ns/0/}location").text
        shows.append(location)

    for shows_chunk in chunks(shows, 50):
        sp.current_user_saved_shows_add(shows=shows_chunk)
        logger.info("Added %d new items to saved shows", len(shows_chunk))


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Spotify Playlist Management Script")
    help_txt = """Command to execute: 'export' to export library items, 
    'import' to import library items, 
    'delete' to delete all library items"""
    parser.add_argument(
        "command", choices=["export", "import", "delete"], help=help_txt
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="File path for import or directory path for export (not needed for delete)",
    )

    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(constants.CONFIG_AUTH)

    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=config["spotify"]["client_id"],
        client_secret=config["spotify"]["client_secret"],
        redirect_uri=config["spotify"]["redirect_uri"],
        scope=" ".join(constants.SCOPES),
        cache_handler=spotipy.cache_handler.CacheFileHandler(
            username=config["spotify"]["username"],
        ),
        show_dialog=True,
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

    user_info = sp.me()
    logger.info("Authenticated as: %s (%s)", user_info["display_name"], user_info["id"])

    if args.command == "import":
        if args.path is None:
            parser.error("The 'import' command requires a path argument.")
        import_playlist(sp, config["spotify"]["username"], args.path)
        import_saved_tracks(sp, args.path)
        import_albums(sp, args.path)
        import_shows(sp, args.path)
    elif args.command == "export":
        if args.path is None:
            parser.error("The 'export' command requires a path argument.")
        export_playlists(sp, config["spotify"]["username"], args.path)
        export_albums(sp, args.path)
        export_shows(sp, args.path)
    elif args.command == "delete":
        delete_all_user_playlists(sp)
        delete_all_saved_tracks(sp)
        delete_all_saved_albums(sp)
        delete_all_saved_shows(sp)


if __name__ == "__main__":
    main()
