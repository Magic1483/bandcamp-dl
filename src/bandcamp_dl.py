
import requests
import re
import os
from typing import List
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
import sys
from time import sleep
from random import randint
from pathlib import Path
# ---------
# This utls download albums from bandcamp.com with title,album name and cover
# tested in VLC and Windws Media Player
# 
# P.S. u can get block by frequent requests, adjust timeouts as needed
# ---------

def sanitize_name(filename):
    keepcharacters = (' ','.','_')
    return "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()


def download(album_link):
    # album url(or sinhle track)
    session = requests.Session()
    session.headers.update({
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.10 Safari/605.1.1"
    })
    r = session.get(album_link)
    if r.status_code == 200:
        links:List = re.findall(r"(https:\/\/t4\.bcbits[^}]*)[\s\S]*?;title&quot;:&quot;([^;,]+)",r.text)
        links = list(map(lambda x: (x[1].replace('&quot',''),x[0]),links))
        
        album_title = re.findall(r"album_title&quot;:&quot;([^;]+)",r.text)[0].replace('&quot','').replace('?','')
        cover_url = re.findall(r"class=\"popupImage\" href=\"(https://f4\.bcbits\.com\/img[^\"]+)",r.text)[0]

        print(f'album_title: {album_title}')

    album_title = sanitize_name(album_title)    
    os.makedirs(album_title.replace('-',''),exist_ok=True)
    # save cover
    r = session.get(cover_url)
    if r.status_code == 200:
        with open(f'{album_title}/cover.jpg','wb') as f:
            f.write(r.content)

    # save tracks
    curr = 0
    while curr != len(links):
        sleep_time = float(randint(200,500)) / 100
        # print(f'sleep {sleep_time}')
        sleep(sleep_time)


        data = session.get(links[curr][1])
        if data.status_code == 200:
            pname = f"{album_title}/{links[curr][0].replace('?','').replace('/','')}.mp3"
            with open(pname,'wb') as f:
                print(f"Download: [{curr+1}/{len(links)}] {links[curr][0]:<30}")
                f.write(data.content)
            
            audio = MP3(pname,ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            audio.tags.delall("APIC")

            audio.tags.add(TIT2(encoding=3, text=links[curr][0]))
            audio.tags.add(TALB(encoding=3, text=album_title))
            audio.tags.add(TPE1(encoding=3, text="The Pirate Bay"))
            
            with open(f'{album_title}/cover.jpg','rb') as img:
                audio.tags.add(APIC(
                    encoding=3,         # 3 is for utf-8
                    mime='image/jpeg',  # image/jpeg or image/png
                    type=3,             # 3 is for the cover image
                    desc=u'Cover',
                    data=img.read()
                ))
            audio.save(v2_version=3)
            curr+=1
        else:
            print(f"error get {links[curr][0]} {data.status_code} {links[curr][1]}")
            # with open("test.html",'wb') as f:   f.write(r.content)
            
def main():
    if len(sys.argv) < 2 or 'http' not in sys.argv[1]:
        print('Usage: bandcamp-dl <album_url>')
    else:
        album_link = sys.argv[1]
        try:
            download(album_link)
        except KeyboardInterrupt:   pass

if __name__ == "__main__":
    main()