# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from threading import Thread
import xml.etree.ElementTree as et
import pygame
import http.client
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
        return u'Авторы сборки неизвестны'
    initial_phrase = ""
    if len(original_names) == 1:
        initial_phrase = u'Автор сборки '
    elif len(original_names) > 0:
        initial_phrase = 'Список авторов сборки: '
    flattened_names = ', '.join([" ".join(n) for n in original_names])
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


def parse_jam_level(html_feed):
    levelint = -1
    parsed_html = BeautifulSoup(html_feed, "html.parser")
    if parsed_html.body is None:
        print("Can't parse response")
        return levelint
    levstr = parsed_html.body.find('div', attrs={'class':'traffic__rate-text'}).text
    try:
        levelint = int(levstr)
    except ValueError as verr:
        pass
    except Exception as ex:
        pass
    return levelint


def build_notifier_loop():
    data = parse_settings("./data.xml")
    url = "http://172.20.20.72:8888/guestAuth/feed.html?itemsType=builds&buildStatus=successful&buildStatus=failed&userKey=guest&itemsCount=2"
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


def traffic_notifier_loop():
    data = parse_settings("./data.xml")
    APP_VERSION = "0.1.0"
    APP_ID = "teamcity-build-notifier"
    USER_AGENT = "{0}/{1} ({2})".format(APP_ID, APP_VERSION,
        "{0}/{1}".format("https://github.com/MikhailUskin", APP_ID))
    previous_level = 0
    while True:
        conn = http.client.HTTPSConnection("www.yandex.ru")
        conn.request("GET", "/", None, {"User-Agent": USER_AGENT})
        resp = str(conn.getresponse().read().decode("utf-8"))
        conn.close()
        current_level = parse_jam_level(resp)
        if current_level >= 7 and previous_level < 7:
            phrase_intro = genintrophrase(data["fail_phrases"])
            text = phrase_intro + ". Уровень пробок " + str(current_level) + " баллов"
            voicemsg("fail_intro.wav", text)  
        elif current_level <= 6 and previous_level > 6:
            phrase_intro = genintrophrase(data["success_phrases"])
            text = phrase_intro + ". Уровень пробок " + str(current_level) + " баллов"
            voicemsg("success_intro.wav", text)
        previous_level = current_level
        time.sleep(10*60)


def init_notifier():
    random.seed()
    pygame.mixer.init()


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


def deploy():
    init_notifier()
    thr1 = Thread(target=build_notifier_loop)
    thr2 = Thread(target=traffic_notifier_loop)
    thr1.start()
    time.sleep(60)
    thr2.start()
    thr1.join()
    thr2.join()


def main():
    try:
        deploy()
    except KeyboardInterrupt:
        clean()


if __name__ == '__main__':
    main()