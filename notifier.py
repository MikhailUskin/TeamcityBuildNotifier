import xml.etree.ElementTree as et
import pygame
import feedparser
import googletrans
import random
import gtts
import time
import sys
import re
import os

def playaudio(path):
    with open(path) as f:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() == True:
            pygame.time.wait(10)

def genvoice(textstr):
    print(textstr)
    msgpath = str(random.randint(1, 10000000)) + ".mp3"
    tts = gtts.gTTS(text=textstr, lang="ru")
    tts.save(msgpath)
    return msgpath


def extractbuildnum(textstr):
    parsed = re.search(r'(#|\.)[\d]{1,}\s', textstr)
    return int(parsed.group(0)[1:-1])


def extractauthors(textstr):
    full_names = []
    match = re.findall(r'by.+?\<br', textstr.replace("\r\n",""))
    if len(match) == 0:
        return full_names
    match = re.findall(r'[\,?\s]{1}.+?[\,|\<]', match[0])
    for g in match:
        name = [n for n in g.replace(",", "").replace(".", " ").replace("<", "").split(' ') if len(n) > 0]
        full_names.append(name)
    return full_names


def voicesuccess(hello_msg, build_name, author_name, build_number, trans):
    authors_name = trans.translate(author_name, src='en', dest='ru').text
    authors_msg = "Автор последнего коммита " + author_name if author_name != "" else ""
    audiopath = genvoice(hello_msg + ". Сборка " + build_name +
             " под номером " + str(build_number) + " завершена. " + authors_msg)
    playaudio("success_intro.wav")
    playaudio(audiopath)
    os.remove(audiopath)


def voicefail(hello_msg, build_name, author_name, build_number, trans):
    authors_name = trans.translate(author_name, src='en', dest='ru').text
    authors_msg = "Автор последнего коммита " + author_name if author_name != "" else ""
    audiopath = genvoice(hello_msg + ". Сборка " + build_name +
             " под номером " + str(build_number) + " сломана. " + authors_msg)
    playaudio("fail_intro.wav")
    playaudio(audiopath)
    os.remove(audiopath)


def getstatus(entry):
    if entry.title.find("successful") != -1:
        return 1
    return 0


def findentry(build_name, feed):
    for entry in feed.entries:
        i = entry.title.find(build_name)
        if i >= 0:
            return entry
    return None


def loop(data):
    url = "http://172.20.20.72:8888/guestAuth/feed.html?itemsType=builds&buildStatus=successful&buildStatus=failed&userKey=guest&itemsCount=2"
    random.seed()
    trans = googletrans.Translator()
    pygame.mixer.init()
    build_number = [0]*len(data["build_names"])
    while True:
        feed = feedparser.parse(url)
        for i, name in enumerate(data["build_names"]):
            entry = findentry(name[0], feed)
            if entry == None:
                continue
            extrbuildnum = extractbuildnum(entry.title)
            if extrbuildnum != build_number[i]:
                author_names = extractauthors(entry.summary)
                if len(author_names) == 0:
                    author_names = [[""]]
                if getstatus(entry) == 1:
                    suspect_name = " ".join(author_names[-1])
                    voicesuccess(data["success_phrases"][random.randint(0, len(data["success_phrases"])-1)], name[1], suspect_name, extrbuildnum, trans)
                else:
                    suspect_name = ""
                    if len(author_names) == 1:
                        suspect_name = " ".join(author_names[-1])
                    voicefail(data["fail_phrases"][random.randint(0, len(data["fail_phrases"])-1)], name[1], suspect_name, extrbuildnum, trans)
                build_number[i] = extrbuildnum
        time.sleep(5)


def clean():
    for item in os.listdir():
        if item.endswith(".mp3"):
            os.remove(item)


def parse_settings(path):
    tree = et.parse(path)
    root = tree.getroot()
    lang = ""
    feed_url = ""
    success_phrases = []
    fail_phrases = []
    build_names = []
    for data in root:
        if (data.tag == "phrases"):
            success_phrases = [p.text for p in data if p.tag == "success"]
            fail_phrases = [p.text for p in data if p.tag == "fail"]
        elif (data.tag == "build"):
            build_names.append([data.attrib["key"], data.text])
        elif (data.tag == "url"):
            feed_url = data.text
        else:
            print("Error - Tag'", data.tag, "' is not recognized")
            exit()
    if feed_url == "":
        print("Error - Feed URL is empty")
        #exit()
    return {"feed_url": feed_url,"lang": lang, \
            "success_phrases": success_phrases, "fail_phrases": fail_phrases, "build_names": build_names}


def main():
    try:
        loop(parse_settings("./data.xml"))
    except KeyboardInterrupt:
        clean()


if __name__ == '__main__':
    main()