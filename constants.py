SCOPES = (
    "playlist-read-collaborative",
    "playlist-read-private",
    "user-library-read",
    "user-library-modify",
    "playlist-modify-private",
    "playlist-modify-public",
)

CONFIG_AUTH = "auth.ini"

PLAYLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<playlist version="1" xmlns="http://xspf.org/ns/0/">
  <title>{{ title }}</title>
{%- if location %}
  <location>{{ location }}</location>
{%- endif %}
  <extension application="https://github.com/debfx/spotify-playlists">
    <public>{{ public | string | lower }}</public>
    <collaborative>{{ collaborative | string | lower }}</collaborative>
    <type>{{ pl_type }}</type>
  </extension>
  <trackList>
{%- for track in tracklist %}
    <track>
      <title>{{ track.title }}</title>
      <creator>{{ track.artists }}</creator>
      <location>{{ track.uri }}</location>
    </track>
{%- endfor %}
  </trackList>
</playlist>
"""

ALBUM_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<album version="1" xmlns="http://xspf.org/ns/0/">
  <albumList>
{%- for album in albumlist %}
    <album>
      <title>{{ album.title }}</title>
      <creator>{{ album.artists }}</creator>
      <location>{{ album.uri }}</location>
    </album>
{%- endfor %}
  </albumList>
</album>
"""

SHOW_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<show version="1" xmlns="http://xspf.org/ns/0/">
  <showList>
{%- for show in showlist %}
    <show>
      <title>{{ show.title }}</title>
      <publisher>{{ show.artists }}</publisher>
      <location>{{ show.uri }}</location>
    </show>
{%- endfor %}
  </showList>
</show>
"""

FILEPATH_SAVED_TRACKS = "__saved_tracks.xspf"
FILEPATH_SAVED_ALBUMS = "__saved_albums.xspf"
FILEPATH_SAVED_SHOWS = "__saved_shows.xspf"
