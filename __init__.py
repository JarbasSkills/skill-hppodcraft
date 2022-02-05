from os.path import join, dirname

import feedparser
from mycroft.util.parse import fuzzy_match
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    MediaType, PlaybackType, ocp_search, ocp_featured_media


class HPPodcraftSkill(OVOSCommonPlaybackSkill):

    def __init__(self):
        super().__init__("HPPodcraft")
        self.supported_media = [MediaType.GENERIC,
                                MediaType.AUDIOBOOK,
                                MediaType.PODCAST]
        self.default_image = join(dirname(__file__), "ui", "bg2.jpg")
        self.skill_icon = join(dirname(__file__), "ui", "logo.png")
        self.default_bg = join(dirname(__file__), "ui", "bg2.jpg")
        data = self.get_streams()
        self.readings = data["readings"]
        self.episodes = data["episodes"]

    def initialize(self):
        # TODO from websettings meta
        if "auth" not in self.settings:
            self.settings["auth"] = "mvbfxt71cwu0zkdwz7h5lx8et8m_bjm0"

    def clean_vocs(self, phrase):
        phrase = self.remove_voc(phrase, "reading")
        phrase = self.remove_voc(phrase, "episode")
        phrase = self.remove_voc(phrase, "lovecraft")
        phrase = self.remove_voc(phrase, "hppodcraft")
        phrase = phrase.strip()
        return phrase

    # common play
    def get_base_score(self, phrase, media_type):
        base_score = 0
        if self.voc_match(phrase, "episode") or \
                self.voc_match(phrase, "reading"):
            base_score += 10
        if self.voc_match(phrase, "hppodcraft"):
            base_score += 50
        elif media_type == MediaType.GENERIC:
            base_score = 0
        if self.voc_match(phrase, "lovecraft"):
            base_score += 30
        return base_score

    @ocp_search()
    def ocp_hppodcraft_playlist(self, phrase, media_type):
        score = self.get_base_score(phrase, media_type)
        if self.voc_match(phrase, "lovecraft"):
            score += 10
        if media_type == MediaType.PODCAST or \
                self.voc_match(phrase, "podcast"):
            score += 10
        elif media_type == MediaType.AUDIOBOOK:
            return
        else:
            score -= 15

        pl = [{
            "match_confidence": fuzzy_match(phrase, k) * 100,
            "media_type": MediaType.PODCAST,
            "uri": v["stream"],
            "title": k,
            "playback": PlaybackType.AUDIO,
            "image": self.default_image,
            "bg_image": self.default_bg,
            "skill_icon": self.skill_icon,
            "author": "HPPodcraft",
            "album": "HPPodcraft"
        } for k, v in self.episodes.items()]

        return [{
            "match_confidence": score,
            "media_type": MediaType.PODCAST,
            "playlist": pl,
            "playback": PlaybackType.AUDIO,
            "skill_icon": self.skill_icon,
            "image": self.default_bg,
            "bg_image": self.default_bg,
            "title": "HPPodcraft (Podcast)",
            "author": "H. P. Lovecraft"
        }]

    @ocp_search()
    def ocp_hppodcraft_readings_playlist(self, phrase, media_type):
        score = self.get_base_score(phrase, media_type)

        if media_type == MediaType.PODCAST:
            return

        pl = [{
            "match_confidence": fuzzy_match(phrase, k) * 100,
            "media_type": MediaType.AUDIOBOOK,
            "uri": v["stream"],
            "title": k,
            "playback": PlaybackType.AUDIO,
            "image": self.default_image,
            "bg_image": self.default_bg,
            "skill_icon": self.skill_icon,
            "author": "HPPodcraft",
            "album": "HPPodcraft"
        } for k, v in self.readings.items()]
        pl = sorted(pl, key=lambda k: k["title"])
        return [{
            "match_confidence": score,
            "media_type": MediaType.AUDIOBOOK,
            "playlist": pl,
            "playback": PlaybackType.AUDIO,
            "skill_icon": self.skill_icon,
            "image": self.default_bg,
            "bg_image": self.default_bg,
            "title": "HPPodcraft (Audiobook Readings)",
            "author": "H. P. Lovecraft"
        }]

    @ocp_featured_media()
    def featured_media(self):
        pl = [{
            "media_type": MediaType.AUDIOBOOK,
            "uri": v["stream"],
            "title": k,
            "playback": PlaybackType.AUDIO,
            "image": self.default_image,
            "bg_image": self.default_bg,
            "skill_icon": self.skill_icon,
            "author": "HPPodcraft",
            "album": "HPPodcraft"
        } for k, v in self.readings.items()]

        pl += [{
            "media_type": MediaType.PODCAST,
            "uri": v["stream"],
            "title": k,
            "playback": PlaybackType.AUDIO,
            "image": self.default_image,
            "bg_image": self.default_bg,
            "skill_icon": self.skill_icon,
            "author": "HPPodcraft",
            "album": "HPPodcraft"
        } for k, v in self.episodes.items()]

        return pl

    # hppodcraft
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
                if "audio" in url["type"]:
                    stream = url["href"]
                    break
            entry = {
                # "summary": bs4.BeautifulSoup(e["summary"], "html.parser").text,
                "summary": e["summary"],
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

        return {"readings": readings,
                "episodes": episodes,
                "originals": originals,
                "commercials": commercial, "comments_show": comments_show,
                "bonus": bonus, "other": other}


def create_skill():
    return HPPodcraftSkill()
