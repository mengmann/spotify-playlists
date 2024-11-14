# Spotify Playlists

Import / export / delete Spotify playlists and more (saved tracks, albums, shows)


## Usage

```bash
usage: spotify-playlists.py [-h] {import,export,delete} [path]

Spotify Playlist Management Script

positional arguments:
  {import,export,delete}
                        Command to execute: 'import' to import a playlist, 'export' to export playlists, 'delete' to delete playlists
  path                  File path for import or directory path for export (not needed for delete)

options:
  -h, --help            show this help message and exit

```

Examples:

* `./spotify-playlists.py export mypath`
* `./spotify-playlists.py import mypath/MyPlaylist.xspf`
* `./spotify-playlists.py import mypath/MyPlaylist.xspf`
* `./spotify-playlists.py delete`


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
