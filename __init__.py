from lingua_franca.parse import extract_number
import feedparser
from ovos_utils.skills.templates.common_play import BetterCommonPlaySkill
from ovos_utils.playback import CPSMatchType, CPSPlayback, CPSMatchConfidence
from os.path import join, dirname
from mycroft.util.parse import fuzzy_match
from ovos_utils.json_helper import merge_dict


class HPPodcraftSkill(BetterCommonPlaySkill):

    def __init__(self):
        super().__init__("HPPodcraft")
        self.supported_media = [CPSMatchType.GENERIC,
                                CPSMatchType.AUDIOBOOK,
                                CPSMatchType.PODCAST]
        # TODO from websettings meta
        if "auth" not in self.settings:
            self.settings["auth"] = "mvbfxt71cwu0zkdwz7h5lx8et8m_bjm0"

        self.default_image = join(dirname(__file__), "ui", "bg2.jpg")
        self.skill_logo = join(dirname(__file__), "ui", "logo.png")
        self.skill_icon = join(dirname(__file__), "ui", "logo.png")
        self.default_bg = join(dirname(__file__), "ui", "bg2.jpg")
        data = self.get_streams()
        self.readings = data["readings"]
        self.episodes = data["episodes"]

    def get_intro_message(self):
        self.speak_dialog("intro")
        self.gui.show_image(self.skill_logo)

    def clean_vocs(self, phrase):
        phrase = self.remove_voc(phrase, "reading")
        phrase = self.remove_voc(phrase, "episode")
        phrase = self.remove_voc(phrase, "lovecraft")
        phrase = self.remove_voc(phrase, "hppodcraft")
        phrase = phrase.strip()
        return phrase

    # common play
    def CPS_search(self, phrase, media_type):
        """Analyze phrase to see if it is a play-able phrase with this skill.

        Arguments:
            phrase (str): User phrase uttered after "Play", e.g. "some music"
            media_type (CPSMatchType): requested CPSMatchType to search for

        Returns:
            search_results (list): list of dictionaries with result entries
            {
                "match_confidence": CPSMatchConfidence.HIGH,
                "media_type":  CPSMatchType.MUSIC,
                "uri": "https://audioservice.or.gui.will.play.this",
                "playback": CPSPlayback.GUI,
                "image": "http://optional.audioservice.jpg",
                "bg_image": "http://optional.audioservice.background.jpg"
            }
        """
        base_score = 0

        if self.voc_match(phrase, "episode") or \
                self.voc_match(phrase, "reading"):
            base_score += 10

        if self.voc_match(phrase, "hppodcraft"):
            base_score += 50

        if self.voc_match(phrase, "lovecraft"):
            base_score += 30
            if self.voc_match(phrase, "episode"):
                base_score += 10
            elif self.voc_match(phrase, "reading"):
                base_score += 20

        num = extract_number(phrase, ordinals=True) or len(self.episodes)
        phrase = self.clean_vocs(phrase)

        results = []
        reading_base = episode_base = base_score
        if media_type == CPSMatchType.AUDIOBOOK:
            reading_base += 10
            episode_base -= 10
        elif media_type == CPSMatchType.PODCAST:
            episode_base += 10
            reading_base -= 5
        i = len(self.episodes)
        for k, v in self.episodes.items():
            score = fuzzy_match(phrase, k) * 100
            score += episode_base
            if i == num:
                score += 15
            if str(num) in k.split(" "):
                score += 10
            if str(num) in k:
                score += 5

            results.append(merge_dict(v, {
                "match_confidence": score,
                "media_type": CPSMatchType.PODCAST,
                "uri": v["stream"],
                "playback": CPSPlayback.AUDIO,
                "image": self.default_image,
                "bg_image": self.default_bg,
                "skill_icon": self.skill_icon,
                "skill_logo": self.skill_logo,
                "author": "HPPodcraft",
                "album": "HPPodcraft"
            }))
            i -= 1

        for k, v in self.readings.items():
            results.append(merge_dict(v, {
                "match_confidence": reading_base + fuzzy_match(phrase, k) * 100,
                "media_type": CPSMatchType.AUDIOBOOK,
                "uri": v["stream"],
                "playback": CPSPlayback.AUDIO,
                "image": self.default_image,
                "bg_image": self.default_bg,
                "skill_icon": self.skill_icon,
                "skill_logo": self.skill_logo,
                "author": "HPPodcraft",
                "album": "HPPodcraft"
            }))

        return results

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

        return {"readings": readings,
                "episodes": episodes,
                "originals": originals,
                "commercials": commercial, "comments_show": comments_show,
                "bonus": bonus, "other": other}


def create_skill():
    return HPPodcraftSkill()
