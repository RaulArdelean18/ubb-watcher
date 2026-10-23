import json, os, sys
from pathlib import Path

import feedparser
import requests

FEED = "https://www.cs.ubbcluj.ro/feed/"
STATE = Path(__file__).with_name("seen.json")
WEBHOOK = os.environ["DISCORD_WEBHOOK"]

# None = toate categoriile; altfel pune doar ce vrei
CATEGORIES = {"Anunţuri studenţi", "Anunţuri burse", "Concursuri pentru studenţi",
              "Oferte firme", "Mobilităţi internaţionale"}

def notify(entries):
    for e in entries:
        cats = ", ".join(t.term for t in e.get("tags", []))
        msg = f"**{e.title}**\n_{cats}_\n{e.link}"
        requests.post(WEBHOOK, json={"content": msg[:1900]}, timeout=20)

def main():
    feed = feedparser.parse(FEED, agent="Mozilla/5.0")
    if feed.bozo and not feed.entries:
        raise RuntimeError(f"Feed invalid: {feed.bozo_exception}")

    first_run = not STATE.exists()
    seen = set() if first_run else set(json.loads(STATE.read_text()))

    new = []
    for e in feed.entries:
        if e.id in seen:
            continue
        cats = {t.term for t in e.get("tags", [])}
        if CATEGORIES is None or cats & CATEGORIES:
            new.append(e)

    if new and not first_run:
        notify(reversed(new))  # cele mai vechi primele

    STATE.write_text(json.dumps(sorted(seen | {e.id for e in feed.entries})))

if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        requests.post(WEBHOOK, json={"content": f"Watcher UBB a eșuat: {ex}"}, timeout=20)
        sys.exit(1)