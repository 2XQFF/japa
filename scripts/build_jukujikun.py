import gzip
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "JMdict_e.gz"
KANJI = ROOT / "data" / "kanji.json"
TARGET = ROOT / "data" / "jukujikun.json"


def values(parent, path):
    return [node.text.strip() for node in parent.findall(path) if node.text]


def unique(items):
    seen = set()
    out = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def priority_score(priorities):
    score = 0
    for priority in priorities:
        if priority.startswith("news"):
            score += 70
        elif priority.startswith("ichi"):
            score += 60
        elif priority.startswith("spec"):
            score += 45
        elif priority.startswith("gai"):
            score += 30
        elif priority.startswith("nf"):
            try:
                score += max(1, 50 - int(priority[2:]))
            except ValueError:
                score += 1
    return score


def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing {SOURCE}. Download JMdict_e.gz first.")

    old_to_new = {}
    if KANJI.exists():
        old_to_new = json.loads(KANJI.read_text(encoding="utf-8")).get("oldToNew", {})

    def normalize_kanji(text):
        return "".join(old_to_new.get(char, char) for char in text)

    root = ET.parse(gzip.open(SOURCE, "rb")).getroot()
    records = []

    for entry in root.findall("entry"):
        reading_elements = entry.findall("r_ele")
        gikun_readings = [
            r_ele
            for r_ele in reading_elements
            if any((value or "").startswith("gikun") for value in values(r_ele, "re_inf"))
        ]
        if not gikun_readings:
            continue

        writings = values(entry, "./k_ele/keb")
        if not writings:
            continue

        all_readings = values(entry, "./r_ele/reb")
        readings = unique(values(r_ele, "reb")[0] for r_ele in gikun_readings if values(r_ele, "reb"))
        restrictions = unique(value for r_ele in gikun_readings for value in values(r_ele, "re_restr"))
        if restrictions:
            writings = [writing for writing in writings if writing in restrictions]

        glosses = unique(values(entry, "./sense/gloss"))
        misc = unique(values(entry, "./sense/misc"))
        info = unique(values(entry, "./k_ele/ke_inf") + [value for r_ele in gikun_readings for value in values(r_ele, "re_inf")])
        priorities = unique(values(entry, "./k_ele/ke_pri") + [value for r_ele in gikun_readings for value in values(r_ele, "re_pri")])

        for writing in writings:
            records.append(
                {
                    "id": values(entry, "ent_seq")[0],
                    "writing": writing,
                    "normalizedWriting": normalize_kanji(writing),
                    "readings": readings,
                    "allReadings": unique(all_readings),
                    "meanings": glosses[:8],
                    "info": info,
                    "misc": misc,
                    "priority": priorities,
                    "score": priority_score(priorities),
                }
            )

    records.sort(key=lambda item: (-item["score"], item["writing"], item["readings"][0] if item["readings"] else ""))

    payload = {
        "source": {
            "name": "JMdict",
            "url": "https://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz",
            "license": "Creative Commons Attribution-ShareAlike 4.0",
            "copyright": "Electronic Dictionary Research and Development Group",
        },
        "records": records,
    }
    TARGET.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {TARGET} with {len(records)} gikun/jukujikun records.")


if __name__ == "__main__":
    main()
