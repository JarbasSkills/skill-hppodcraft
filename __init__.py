from os.path import join, dirname

import feedparser
from ovos_utils import timed_lru_cache
from ovos_utils.ocp import PlaybackType, MediaType

from ovos_workshop.decorators.ocp import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


class HPPodcraftSkill(OVOSCommonPlaybackSkill):
    def __init__(self, *args, **kwargs):
        self.supported_media = [MediaType.AUDIOBOOK,
                                MediaType.PODCAST]

        self.default_image = join(dirname(__file__), "ui", "bg2.jpg")
        self.skill_icon = join(dirname(__file__), "ui", "logo.png")
        self.default_bg = join(dirname(__file__), "ui", "bg2.jpg")
        super().__init__(*args, **kwargs)

    def initialize(self):
        # TODO from websettings meta
        if "auth" not in self.settings:
            self.settings["auth"] = "mvbfxt71cwu0zkdwz7h5lx8et8m_bjm0"
        self.get_streams()  # trigger keyword registering / pre-cache

    @property
    def readings(self):
        return self.get_streams()["readings"]

    @property
    def episodes(self):
        return self.get_streams()["episodes"]

    def ocp_hppodcraft_playlist(self, media_type, score=100):
        score = min(100, score)
        if media_type == MediaType.AUDIOBOOK:
            pl = [{
                "match_confidence": score,
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

            yield {
                "match_confidence": score,
                "media_type": MediaType.AUDIOBOOK,
                "playlist": pl,
                "playback": PlaybackType.AUDIO,
                "skill_icon": self.skill_icon,
                "image": self.default_bg,
                "bg_image": self.default_bg,
                "title": "HPPodcraft (Audiobook Readings)",
                "author": "H. P. Lovecraft"
            }
        else:
            pl = [{
                "match_confidence": score,
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

            yield {
                "match_confidence": score,
                "media_type": MediaType.PODCAST,
                "playlist": pl,
                "playback": PlaybackType.AUDIO,
                "skill_icon": self.skill_icon,
                "image": self.default_bg,
                "bg_image": self.default_bg,
                "title": "HPPodcraft (Podcast)",
                "author": "H. P. Lovecraft"
            }

    @ocp_featured_media()
    def featured_media(self):
        return [
            {
                "match_confidence": 100,
                "media_type": MediaType.PODCAST,
                "uri": v["stream"],
                "title": k,
                "playback": PlaybackType.AUDIO,
                "image": self.default_image,
                "bg_image": self.default_bg,
                "skill_icon": self.skill_icon,
                "author": "HPPodcraft",
                "album": "HPPodcraft"
            } for k, v in self.episodes.items()] + [
            {
                "match_confidence": 100,
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

    @ocp_search()
    def search_db(self, phrase, media_type=MediaType.GENERIC):
        base_score = 10 if media_type == MediaType.PODCAST else 0
        entities = self.ocp_voc_match(phrase)
        base_score += 20 * len(entities)

        title = entities.get("podcast_episode")
        book = entities.get("book_name")
        n = int(entities.get("episode_number", 0))
        skill = "podcast_streaming_provider" in entities  # skill matched

        if skill:
            base_score += 25
            yield self.ocp_hppodcraft_playlist(media_type, base_score)

        # only search db if user explicitly requested a known episode / book name
        if book and (media_type == MediaType.AUDIOBOOK or
                     media_type == MediaType.GENERIC or
                     skill):
            for k, v in self.readings.items():
                if book.lower() in k.lower():
                    yield {
                        "match_confidence": min(100,
                                                base_score + 35 if media_type == MediaType.AUDIOBOOK
                                                else base_score + 15),
                        "media_type": MediaType.AUDIOBOOK,
                        "uri": v["stream"],
                        "title": k,
                        "playback": PlaybackType.AUDIO,
                        "image": self.default_image,
                        "bg_image": self.default_bg,
                        "skill_icon": self.skill_icon,
                        "author": "HPPodcraft",
                        "album": "HPPodcraft"
                    }

        if title and (media_type == MediaType.PODCAST or
                      media_type == MediaType.GENERIC or
                      skill):
            if n:
                base_score += 15
            for k, v in self.episodes.items():
                if n and str(n) not in k:
                    continue
                if title.lower() in k.lower():
                    yield {
                        "match_confidence": min(100,
                                                base_score + 35 if media_type == MediaType.PODCAST else
                                                base_score + 15),
                        "media_type": MediaType.PODCAST,
                        "uri": v["stream"],
                        "title": k,
                        "playback": PlaybackType.AUDIO,
                        "image": self.default_image,
                        "bg_image": self.default_bg,
                        "skill_icon": self.skill_icon,
                        "author": "HPPodcraft",
                        "album": "HPPodcraft"
                    }

    # hppodcraft
    @timed_lru_cache(seconds=3600)
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
                episodes[e["title"].replace('–', "-")] = entry
            elif e["title"].startswith("Reading"):
                norm = e["title"].replace('–', "-").split("-")[1].strip()
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

        self.register_ocp_keyword(MediaType.AUDIOBOOK,
                                  "book_name", list(readings))
        self.register_ocp_keyword(MediaType.PODCAST,
                                  "podcast_name", ["HPPodcraft"])
        self.register_ocp_keyword(MediaType.PODCAST,
                                  "podcast_episode", [e.split("-")[1].strip() for e in episodes if "-" in e])
        self.register_ocp_keyword(MediaType.PODCAST,
                                  "episode_number",
                                  [e.split("-")[0].split("Episode")[-1].strip("! ") for e in episodes if
                                   "Episode" in e])
        self.register_ocp_keyword(MediaType.PODCAST,
                                  "podcast_streaming_provider",
                                  ["HPPodcraft", "HP Podcraft", "H. P. Podcraft"])
        # self.export_ocp_keywords_csv("hppodcraft.csv")
        return {"readings": readings,
                "episodes": episodes,
                "originals": originals,
                "commercials": commercial, "comments_show": comments_show,
                "bonus": bonus, "other": other}


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus

    s = HPPodcraftSkill(bus=FakeBus(), skill_id="t.fake")

    for r in s.search_db("cool air"):
        print(r)
        # {'match_confidence': 55, 'media_type': <MediaType.AUDIOBOOK: 4>, 'uri': 'https://c10.patreonusercontent.com/4/patreon-media/p/post/18594042/24cb07902ba647de8dc9fac2c8bfa13b/eyJhIjoxLCJwIjoxfQ%3D%3D/1.mp3?token-time=1706313600&token-hash=0EUi-VOVb9EO41YZy7LiNla8rc6xidlUrGS-7ZktnvA%3D', 'title': 'Cool Air', 'playback': <PlaybackType.AUDIO: 2>, 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-hppodcraft/ui/bg2.jpg', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-hppodcraft/ui/bg2.jpg', 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'author': 'HPPodcraft', 'album': 'HPPodcraft'}
        # {'match_confidence': 55, 'media_type': <MediaType.PODCAST: 6>, 'uri': 'https://c10.patreonusercontent.com/4/patreon-media/p/post/18593309/328a2202e258488d9d5e01bb2fcc4a81/eyJhIjoxLCJwIjoxfQ%3D%3D/1.mp3?token-time=1706313600&token-hash=uqTS0ab-DM1XE6D34CsO1fl9bj6-DAGryn21nKWcIGM%3D', 'title': 'Episode 41 - Cool Air', 'playback': <PlaybackType.AUDIO: 2>, 'image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-hppodcraft/ui/bg2.jpg', 'bg_image': '/home/miro/PycharmProjects/OCP_sprint/skills/skill-hppodcraft/ui/bg2.jpg', 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'author': 'HPPodcraft', 'album': 'HPPodcraft'}
