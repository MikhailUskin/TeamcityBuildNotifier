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


def voicemsg(intropath, textmsg):
    audiopath = genvoice(textmsg)
    playaudio(intropath)
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

def genauthorsphrase(original_names):
    if len(original_names) == 0:
        return "Авторы сборки неизветсны "  
    initial_phrase = ""
    if len(original_names) == 1:
        initial_phrase = "Автор сборки "
    elif len(original_names) > 0:
        initial_phrase = "Список авторов сборки: "
    flattened_names = ", ".join([" ".join(n) for n in original_names])
    trans = googletrans.Translator()
    return initial_phrase + trans.translate(flattened_names, src='en', dest='ru').text
    
    
def genintrophrase(original_phrases):
    return original_phrases[random.randint(0, len(original_phrases)-1)]


def voicestatus(entry, data, build_name, build_num):
    author_names = extractauthors(entry.summary)
    if len(author_names) == 0:
        author_names = [[""]]
    phrase_authors = genauthorsphrase(author_names)
    if getstatus(entry) == 1:
        phrase_intro = genintrophrase(data["success_phrases"])
        text = phrase_intro + ". Сборка " + build_name + \
             " под номером " + str(build_num) + " завершена. " + phrase_authors
        voicemsg("success_intro.wav", text)    
    else:
        phrase_intro = genintrophrase(data["fail_phrases"])
        text = phrase_intro + ". Сборка " + build_name + \
             " под номером " + str(build_num) + " сломана. " + phrase_authors
        voicemsg("fail_intro.wav", text)


def loop(data):
    url = "http://172.20.20.72:8888/guestAuth/feed.html?itemsType=builds&buildStatus=successful&buildStatus=failed&userKey=guest&itemsCount=2"
    random.seed()
    pygame.mixer.init()
    build_number = [0]*len(data["build_names"])
    while True:
        feed = feedparser.parse(url)
        for i, build_name in enumerate(data["build_names"]):
            entry = findentry(build_name[0], feed)
            if entry == None:
                continue
            build_num = extractbuildnum(entry.title)
            if build_num != build_number[i]:
                voicestatus(entry, data, build_name[1], build_num)
                build_number[i] = build_num
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