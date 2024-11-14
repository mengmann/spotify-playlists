# Spotify Playlists

Import / export / delete Spotify playlists and more (saved tracks, albums, shows)


## Usage

```bash
usage: spotify-playlists.py [-h] {export,import,delete} [path]

Spotify Playlist Management Script

positional arguments:
  {export,import,delete}
                        Command to execute: 'export' to export library items, 'import' to import library items, 'delete' to delete all library items
  path                  File path for import or directory path for export (not needed for delete)

options:
  -h, --help            show this help message and exit

```

**Examples:**

* export playlists, saved tracks, albums and shows:
```bash
./spotify-playlists.py export mypath
```

* import playlists, saved tracks, albums and shows from directory:
```bash
./spotify-playlists.py import mypath
```

* just import a single playlist:
```bash
./spotify-playlists.py import mypath/MyPlaylist.xspf
```

* delete playlists, saved tracks, albums and shows:
```bash
./spotify-playlists.py delete
```

## Install

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
source venv/bin/activate
```

## Setup

* Create an app on [Spotify My Dashboard](https://developer.spotify.com/dashboard/applications)
* Redirect URI can be anything (e.g. `http://localhost/`)
* Copy auth.ini.example to auth.ini
* Insert the client id, token, redirect uri and Spotify username in auth.ini
