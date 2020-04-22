#!/usr/bin/env python3

# import required modules
import argparse
import sys
import os
import json
import urllib
import ffmpeg
from pymkv import MKVFile
from pyimgur import Imgur
from pystreamable import StreamableApi
from PIL import Image
import pyperclip
import shutil

def main(imdb, filename, source, mega, time, config):
    if imdb is None:
        imdb = input('IMDB ID:\n')
    if filename is None:
        filename = input('Video filename:\n')
    if source is None:
        source = input('Source URL:\n')
    if mega is None:
        mega = input('Mega link:\n')
    clear()
    config = load_config(config)
    tmp_dir = create_tmp_dir()
    create_sample_videos(filename, time, tmp_dir)
    create_screenshots(filename, time, tmp_dir)
    links = upload(config, tmp_dir)
    imdb_info = get_imdb_info(imdb, config)
    mediainfo = get_mediainfo(filename)
    source_name = get_source_name(source)
    screen_height = get_image_size(tmp_dir)
    generate_text(imdb_info, mediainfo, links, screen_height, source, source_name, mega)
    cleanup(tmp_dir)

# helper functions
def load_config(config):
    print ('Loading config...')
    try:
        with open(config) as config_file:
            data = json.load(config_file)
        if all(value == "" for value in data.values()):
        	sys.exit (f'Error! Please specify api keys and streamable login in "config.json" before running, exiting.')
        else:
            return data
    except FileNotFoundError:
        sys.exit (f'File "{config}" does not exist! Exiting.')

def create_tmp_dir():
    print ('Creating tmp dir...')
    current_working_dir = os.getcwd()
    path = os.path.join(current_working_dir, 'tmp')
    if not os.path.isdir(path):
        try:
            os.mkdir(path)
        except OSError:
            sys.exit ('Creation of tmp folder failed! Exiting.')
    return path

def get_imdb_info(imdb, config):
    print ('Retrieving info from imdb...')
    omdb_api_key = config['omdb_api_key']
    url = f'http://www.omdbapi.com/?apikey={omdb_api_key}&i={imdb}'
    try:
        data = json.load(urllib.request.urlopen(url))
        return data
    except urllib.error.URLError as e:
        sys.exit (f'{e.reason}! Exiting.')

def get_mediainfo(filename):
    print ('Retrieving mediainfo...')
    try:
        mediainfo = os.popen("mediainfo " + filename).read()
        return mediainfo
    except:
        sys.exit ('Error retrieving mediainfo! Exiting.')

def create_screenshots(filename, time, tmp_dir):
    print ('Creating screenshots...')
    for i in range(1, 5):
        file = f'screen-0{i}.jpeg'
        out = os.path.join(tmp_dir, file)
        try:
            (
                ffmpeg
                .input(filename, ss=time*i)
                .output(out, vframes=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            print(e.stderr.decode(), file=sys.stderr)
            sys.exit(1)

def create_sample_videos(filename, time, tmp_dir):
    print ('Creating sample videos...')
    mkv = MKVFile(filename)
    ts_1 = (time - 10, time + 20)
    ts_2 = (time*2 - 10, time*2 + 20)
    try:
        mkv.split_timestamp_parts([ts_1, ts_2])
    except TypeError:
        sys.exit ('Invalid timestamps! Exiting.')
    out = os.path.join(tmp_dir, 'sample.mkv')
    mkv.mux(out)
    clear()

def upload(config, tmp_dir):
    print ('Uploading screens and sample videos...')
    links = {}
    imgur_client_id = config['imgur_client_id']
    imgur = Imgur(imgur_client_id)
    for i in range(1, 5):
        file = f'screen-0{i}.jpeg'
        path = os.path.join(tmp_dir, file)
        try:
            links[file] = imgur.upload_image(path).link
        except:
            sys.exit ('Error uploading to Imgur! Exiting.')
    streamable_username = config['streamable_username']
    streamable_password = config['streamable_password']
    streamable = StreamableApi(streamable_username, streamable_password)
    for i in range(1, 3):
        file = f'sample-00{i}.mkv'
        path = os.path.join(tmp_dir, file)
        try:
            links[file] = f'https://streamable.com/{streamable.upload_video(path)["shortcode"]}'
        except:
            sys.exit ('Error uploading to Streamable! Exiting.')
    return links

def get_source_name(source):
    if '1337x' in source:
        return '1337x'
    elif 'rarbg' in source:
        return 'RARBG'
    elif 'torrentgalaxy' in source:
        return 'TGx'
    elif 'nyaa.si' in source:
        return 'Nyaa.si'
    else:
        return input('Input source name:\n')

def get_image_size(tmp_dir):
    file = f'screen-01.jpeg'
    path = os.path.join(tmp_dir, file)
    try:
        (width, height) = Image.open(path).size
    except FileNotFoundError:
        sys.exit (f'File {file} not found! Exiting.')
    height_out = round(height/width*500)
    return height_out

def generate_text(imdb_info, mediainfo, links, screen_height, source, source_name, mega):
    if imdb_info['Response']=='False':
        sys.exit (imdb_info['Error'])
    else:
        out_text = f'''[center][img]{imdb_info['Poster']}[/img][/center]

[center][size=150][color=#FF0000][b]{imdb_info['Title']} ({imdb_info['Year']})[/b][/color][/size][/center]

[color=#FF8000][b]Director[/b][/color]: {imdb_info['Director']}
[color=#FF8000][b]Writers[/b][/color]: {imdb_info['Writer']}
[color=#FF8000][b]Stars[/b][/color]: {imdb_info['Actors']}

[color=#FF8000][b]Runtime[/b][/color]: {imdb_info['Runtime']} (taken from IMDb)
[color=#FF8000][b]Genre[/b][/color]: {imdb_info['Genre']}

[color=#FF8000][b]Rating[/b][/color]: {imdb_info['imdbRating']}/10* (may differ)
[color=#FF8000][b]Votes[/b][/color]: {imdb_info['imdbVotes']} (may differ)

[color=#FF8000][b]Release Date[/b][/color]: {imdb_info['Released']} (taken from IMDb)
[color=#FF8000][b]Viewer Rating (TV/MPAA)[/b][/color]: {imdb_info['Rated']} (taken from IMDb)

[color=#FF8000][b]Summary[/b][/color]: [i]{imdb_info['Plot']}[/i]

[color=#FF8000][b]Links[/b][/color]: [b][url=https://www.imdb.com/title/{imdb_info['imdbID']}]IMDb ({imdb_info['imdbID']})[/url][/b], [b][url={source}]{source_name} (Screenshots, MediaInfo, etc.)[/url][/b]

[fimg=500,{screen_height}]{links['screen-01.jpeg']}[/fimg] [fimg=500,{screen_height}]{links['screen-02.jpeg']}[/fimg]

[fimg=500,{screen_height}]{links['screen-03.jpeg']}[/fimg] [fimg=500,{screen_height}]{links['screen-04.jpeg']}[/fimg]

[b][url={links['sample-001.mkv']}]Sample 1[/url][/b], [b][url={links['sample-002.mkv']}]Sample 2[/url][/b]

[color=#FF8000][b]MediaInfo[/b][/color]:
[mediainfo]{mediainfo}[/mediainfo][color=#0080FF][b]Direct Download Links[/b][/color]:
[hide][b64]{mega}[/b64][/hide]
Enjoy!'''
        pyperclip.copy(out_text)
        with open('out.txt', 'w') as f:
            f.write(out_text)
        print ('Success!\nText has been copied to clipboard and saved to "out.txt"')

def cleanup(tmp_dir):
    shutil.rmtree(tmp_dir)

def clear(): 
    if os.name == 'nt': 
        _ = os.system('cls') 
    else: 
        _ = os.system('clear')

# arguments
parser = argparse.ArgumentParser(description='Generate BBcode for uploading')
parser.add_argument(
    '--imdb', type=str, default=None, help='IMDB ID')
parser.add_argument(
    '--filename', type=str, default=None, help='Video filename')
parser.add_argument(
    '--source', type=str, default=None, help='Source (torrents, etc)')
parser.add_argument(
    '--mega', type=str, default=None, help='Mega link')
parser.add_argument(
    '--time', type=int, default=1200, help='Screenshot time offset in seconds')
parser.add_argument(
    '--config', type=str, default='config.json', help='Specify config file')

# running script
if __name__ == '__main__':
    args = parser.parse_args()
    main(args.imdb, args.filename, args.source, args.mega, args.time, args.config)
