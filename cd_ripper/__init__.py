import json
import subprocess
import pathlib
from typing import Any, Dict, List, Optional, Tuple

import plac
import tqdm


def load_album_config_file(json_file: pathlib.Path) -> Dict[str, Any]:
    """Unpack album configuration information from .json file."""
    with json_file.open('r') as io_obj:
        return json.load(io_obj)


def wav_to_mp3(wav_file: pathlib.Path, keep_wav: bool = True) -> pathlib.Path:
    """Convert .wav file to .mp3 file using ffmpeg."""
    wav_file = wav_file.resolve()
    if not wav_file.is_file():
        raise FileNotFoundError(wav_file)

    mp3_file = wav_file.parent / (wav_file.stem + ".mp3")

    ffmpeg_command = f"ffmpeg -hide_banner -loglevel error "\
                   + f"-i \"{wav_file}\" -acodec mp3 \"{mp3_file}\""
    subprocess.run(ffmpeg_command, shell=True, check=True)
    if mp3_file.is_file() and not keep_wav:
        wav_file.unlink()

    return mp3_file


def match_titles_to_files(
        title_list: List[str],
        directory: pathlib.Path) -> List[Tuple[str, pathlib.Path]]:
    """Create mapping between ordered titles & music files in given directory."""
    music_files = [f for f in directory.iterdir() if f.suffix in ['.wav', '.mp3']]
    mapping = []

    if len(title_list) != len(music_files):
        raise ValueError(
            f"Found {len(music_files)} music files, "
            f"but given {len(title_list)} titles.")

    for i, title in enumerate(title_list[::-1]):
        track_number = len(title_list) - i
        possible_tracks = [f for f in music_files
                           if (str(track_number) in f.stem or title in f.stem)]
        if len(possible_tracks) > 1:
            raise RuntimeError(
                f"Found multiple music files matching {track_number}-"
                f"{title}: \n{','.join(possible_tracks)}")

        elif len(possible_tracks) == 0:
            raise RuntimeError(
                f"Found no music files matching {track_number}-{title}")

        else:
            music_files = [m for m in music_files if m != possible_tracks[0]]

        mapping.append((title, possible_tracks[0]))

    return mapping[::-1]


def add_metadata(
        mp3_file: pathlib.Path,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        date: Optional[str] = None,
        track_num: Optional[int] = None) -> None:
    """Add metadata to .mp3 file using mid3v2."""
    if not mp3_file.resolve().is_file():
        raise FileNotFoundError(mp3_file.resolve())

    mid3v2_command = "mid3v2"
    if artist is not None:
        mid3v2_command += f" -a \"{artist}\""
    if album is not None:
        mid3v2_command += f" -A \"{album}\""
    if title is not None:
        mid3v2_command += f" -t \"{title}\""
    if genre is not None:
        mid3v2_command += f" -g \"{genre}\""
    if date is not None:
        mid3v2_command += f" -y \"{date}\""
    if track_num is not None:
        mid3v2_command += f" -T \"{track_num}\""

    mid3v2_command += f" \"{mp3_file.resolve()}\""
    subprocess.run(mid3v2_command, shell=True, check=True)


def show_metadata(mp3_file: pathlib.Path) -> None:
    """Show current metadata associated with given mp3 file."""
    if not mp3_file.resolve().is_file():
        raise FileNotFoundError(mp3_file.resolve())

    mid3v2_command = f"mid3v2 -l {mp3_file.resolve()}"
    subprocess.run(mid3v2_command, shell=True, check=True)


@plac.annotations(
    album_directory=plac.Annotation(
        "directory containing songs from album", type=pathlib.Path),
    config_json=plac.Annotation(
        "json-compliant album configuration file - if not given, loads from album_directory",
        "option",
        "cf",
        type=pathlib.Path),
)
def populate_album_metadata(
        album_directory: pathlib.Path,
        config_json: Optional[pathlib.Path] = None) -> None:
    """Given folder of music and configuration data, add metadata to album music.

    Performs the following steps:
    1. Loads metadata from config.json file
    2. Converts any .wav files to .mp3
    3. Matches metadata titles to .mp3 files
    4. Adds metadata to each .mp3 file
    """
    # Argument checking
    if not album_directory.is_dir():
        raise FileNotFoundError(album_directory.resolve())

    if config_json is None:
        try:
            config_json = [f for f in album_directory.iterdir()
                           if f.suffix == '.json'][0]
        except IndexError:
            raise FileNotFoundError(
                "No .json config file found in album, and not provided at CLI")

    elif not config_json.is_file():
        raise FileNotFoundError(config_json.resolve())

    print(f"(1) Loading album metadata from {config_json.resolve()}")
    album_metadata = load_album_config_file(config_json)
    kwargs = {}  # Keywords eventually passed to add_metadata
    for key in ['artist', 'album', 'genre', 'date']:
        kwargs[key] = album_metadata[key] if key in album_metadata else None
    
    print("(2) Converting .wav files to .mp3")
    files = list(album_directory.iterdir())
    for wav_file in tqdm.tqdm(files):
        if wav_file.suffix == '.wav':
            wav_to_mp3(wav_file, keep_wav=False)

    print("(3) Attempting to match metadata song titles with files")
    mapping = match_titles_to_files(album_metadata['songs'], album_directory)

    print("(4) Adding metadata to .mp3 files")
    track_num = 1
    for title, mp3_file in tqdm.tqdm(mapping):
        add_metadata(
            mp3_file=mp3_file, title=title, track_num=track_num, **kwargs)
        track_num += 1


if __name__ == '__main__':
    plac.call(populate_album_metadata)
