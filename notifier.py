from playsound import playsound
import feedparser
import random
import gtts
import time
import os

def voicemsg(textstr):
    msgpath = str(random.randint(1,10000000)) + ".mp3"
    tts = gtts.gTTS(text=textstr, lang="en")
    tts.save(msgpath)
    with open(msgpath) as f:
        playsound(msgpath)
    os.remove(msgpath)

def voicetag(feed):
    for post in feed.entries:
        print(post.title)
        voicemsg(post.title)

def loop(url):
    while True:
        voicetag(feedparser.parse(url))
        time.sleep(5)

def clean():
    for item in os.listdir():
        if item.endswith(".mp3"):
            os.remove(item)

url= "https://feeds2.feedburner.com/TheGeeksOf3d"  # RSS feed URL

def main():
    try:
        loop(url)
    except KeyboardInterrupt:
        clean()

if __name__ == '__main__':
    main()