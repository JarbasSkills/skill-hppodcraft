from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel, CPSMatchType
from mycroft.util.parse import match_one
from lingua_franca.parse import extract_number
import feedparser
import random
import re
from os.path import join, dirname


class HPPodcraftSkill(CommonPlaySkill):

    def __init__(self):
        super().__init__("HPPodcraft")
        self.supported_media = [CPSMatchType.GENERIC,
                                CPSMatchType.AUDIOBOOK,
                                CPSMatchType.PODCAST]
        # TODO from websettings meta
        if "auth" not in self.settings:
            self.settings["auth"] = "mvbfxt71cwu0zkdwz7h5lx8et8m_bjm0"

        self.logo = join(dirname(__file__), "ui", "logo.jpg")
        self.bg = join(dirname(__file__), "ui", "bg2.jpg")
        data = self.get_streams()
        self.readings = list(data["readings"].keys())
        self.readings.reverse()
        self.episodes = list(data["episodes"].keys())
        self.episodes.reverse()

    def initialize(self):
        self.add_event('skill-hppodcraft.jarbasskills.home',
                       self.handle_homescreen)

    def get_intro_message(self):
        self.speak_dialog("intro")
        self.gui.show_image(self.logo)

    def remove_voc(self, utt, voc_filename, lang=None):
        lang = lang or self.lang
        cache_key = lang + voc_filename

        if cache_key not in self.voc_match_cache:
            self.voc_match(utt, voc_filename, lang)

        if utt:
            # Check for matches against complete words
            for i in self.voc_match_cache[cache_key]:
                # Substitute only whole words matching the token
                utt = re.sub(r'\b' + i + r"\b", "", utt)

        return utt

    def clean_vocs(self, phrase):
        phrase = self.remove_voc(phrase, "reading")
        phrase = self.remove_voc(phrase, "episode")
        phrase = self.remove_voc(phrase, "lovecraft")
        phrase = self.remove_voc(phrase, "hppodcraft")
        phrase = phrase.strip()
        return phrase

    # homescreen
    def handle_homescreen(self, message):
        pass  # TODO selection menu

    # common play
    def CPS_match_query_phrase(self, phrase, media_type):
        original = phrase
        match = None
        reading = False
        title = None
        num = False

        if self.voc_match(phrase, "lovecraft"):
            match = CPSMatchLevel.ARTIST

        if media_type == CPSMatchType.PODCAST and \
                self.voc_match(original, "lovecraft"):
            # default to latest
            title = self.episodes[-1]
            match = CPSMatchLevel.TITLE

            if self.voc_match(original, "episode") :
                # match episode number
                num = extract_number(original.split("episode")[0], ordinals=True)
                if num is not False and num < len(self.episodes):
                    title = self.episodes[num - 1]
                    match = CPSMatchLevel.EXACT

        elif media_type == CPSMatchType.AUDIOBOOK and \
                self.voc_match(original, "lovecraft"):
            title = random.choice(self.readings)
            match = CPSMatchLevel.CATEGORY

        phrase = self.clean_vocs(phrase)

        name, score = match_one(phrase, self.readings)
        name2, score2 = match_one(phrase.split("episode")[0], self.episodes)

        # READING / AUDIOBOOK
        if score >= 0.5 and not self.voc_match(original, "episode") and \
                media_type != CPSMatchType.PODCAST:
            title = name
            reading = True
            if match:
                match = CPSMatchLevel.MULTI_KEY
                if score >= 0.8:
                    match = CPSMatchLevel.EXACT
            else:
                if score >= 0.8:
                    match = CPSMatchLevel.EXACT
                else:
                    match = CPSMatchLevel.TITLE

        # PODCAST
        elif score2 >= 0.5 and not num and media_type != CPSMatchType.AUDIOBOOK:
            title = name2
            reading = False
            if match:
                match = CPSMatchLevel.MULTI_KEY
                if score2 >= 0.8:
                    match = CPSMatchLevel.EXACT
            else:
                if score2 >= 0.8:
                    match = CPSMatchLevel.EXACT
                else:
                    match = CPSMatchLevel.TITLE

        if title and self.voc_match(original, "hppodcraft"):
            match = CPSMatchLevel.EXACT

        if match is not None:
            return (phrase, match, {"reading": reading,
                                    "title": title,
                                    "image": self.logo,
                                    "background": self.bg})
        return None

    def CPS_start(self, phrase, data):
        title = data["title"]
        streams = self.get_streams()
        if data["reading"]:
            data = streams["readings"][title]
        else:
            data = streams["episodes"][title]
        self.audioservice.play(data["stream"])
        self.CPS_send_status(**data)

    def get_streams(self):
        url = "https://www.patreon.com/rss/witchhousemmedia?auth=" + \
              self.settings["auth"]

        data = feedparser.parse(url)

        episodes = {}
        readings = {}
        comments_show = {}
        bonus = {}
        originals = {}
        commercial = {}
        other = {}

        for e in data.entries:
            stream = None
            for url in e["links"]:
                if url["type"] == 'audio/mpeg':
                    stream = url["href"]
                    break
            entry = {
                #"summary": bs4.BeautifulSoup(e["summary"], "html.parser").text,
                "summary":e["summary"],
                "title": e["title"],
                "stream": stream,
                "date": e['published']
            }

            if e["title"].startswith("Episode"):
                episodes[e["title"]] = entry
            elif e["title"].startswith("Reading"):
                norm = e["title"].split("–")[-1].strip()
                if "-" in norm:
                    norm = "-".join(norm.split("-")[1:]).strip()
                readings[norm] = entry
            elif e["title"].startswith("Comments Show"):
                comments_show[e["title"]] = entry
            elif e["title"].startswith("Bonus"):
                bonus[e["title"]] = entry
            elif e["title"].startswith("Original Fiction"):
                norm = e["title"].split("–")[-1].strip()
                if "-" in norm:
                    norm = "-".join(norm.split("-")[1:]).strip()
                originals[norm] = entry
                readings[norm] = entry
            elif "– Commercial Spot" in e["title"]:
                commercial[e["title"]] = entry
            else:
                other[e["title"]] = entry

        return {"readings": readings, "episodes": episodes,
                "originals": originals,
                "commercials": commercial, "comments_show": comments_show,
                "bonus": bonus, "other": other}


def create_skill():
    return HPPodcraftSkill()
