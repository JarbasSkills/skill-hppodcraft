import feedparser
from pprint import pprint


def get_streams(auth="mvbfxt71cwu0zkdwz7h5lx8et8m_bjm0"):
    url = "https://www.patreon.com/rss/witchhousemmedia?auth=" + \
          auth

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

pprint(get_streams()["readings"])