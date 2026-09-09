import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "krdict-json"
TARGET = ROOT / "data" / "words.json"
MAX_MEANINGS = 12
EMPTY_MARKERS = {"", "없음"}


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def unique(values):
    seen = set()
    out = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def feature_value(node, key):
    for feature in as_list(node.get("feat") if isinstance(node, dict) else None):
        if isinstance(feature, dict) and feature.get("att") == key:
            return html.unescape(feature.get("val", "")).strip()
    return ""


def lemma_value(entry):
    for lemma in as_list(entry.get("Lemma") if isinstance(entry, dict) else None):
        if not isinstance(lemma, dict):
            continue
        feature = lemma.get("feat")
        if isinstance(feature, dict) and feature.get("att") == "writtenForm":
            return html.unescape(feature.get("val", "")).strip()
        for item in as_list(feature):
            if isinstance(item, dict) and item.get("att") == "writtenForm":
                return html.unescape(item.get("val", "")).strip()
    return ""


def clean_term(value):
    value = html.unescape(value).strip()
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n。;；")


def split_written_forms(value):
    return [
        clean_term(part)
        for part in re.split(r"[・･,，、/／]", value)
        if clean_term(part)
    ]


def japanese_entries(value):
    entries = []
    for segment in re.split(r"[。;；]", html.unescape(value)):
        segment = clean_term(segment)
        if not segment:
            continue
        match = re.match(r"(.+?)【(.+?)】", segment)
        if match:
            reading = clean_term(match.group(1))
            for term in split_written_forms(match.group(2)):
                entries.append({"term": term, "reading": reading})
        else:
            entries.append({"term": segment, "reading": ""})
    return entries


def reading_sort_key(record):
    return (
        0 if record["reading"] else 1,
        len(record["term"]),
        record["term"],
        record["reading"],
    )


def clean_meta(values):
    return [value for value in unique(values) if value not in EMPTY_MARKERS]


def main():
    if not SOURCE_DIR.exists():
        raise SystemExit(f"Missing {SOURCE_DIR}. Download and extract krdict-json first.")

    records_by_key = {}
    for path in sorted(SOURCE_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data["LexicalResource"]["Lexicon"]["LexicalEntry"]
        for entry in as_list(entries):
            korean = lemma_value(entry)
            if not korean:
                continue
            level = feature_value(entry, "vocabularyLevel")
            part_of_speech = feature_value(entry, "partOfSpeech")
            for sense in as_list(entry.get("Sense") if isinstance(entry, dict) else None):
                for equivalent in as_list(sense.get("Equivalent") if isinstance(sense, dict) else None):
                    if feature_value(equivalent, "language") != "일본어":
                        continue
                    japanese = feature_value(equivalent, "lemma")
                    for item in japanese_entries(japanese):
                        term = item["term"]
                        reading = item["reading"]
                        if not term or len(term) > 40:
                            continue
                        key = f"{term}\t{reading}"
                        record = records_by_key.setdefault(
                            key,
                            {
                                "term": term,
                                "reading": reading,
                                "meanings": [],
                                "partsOfSpeech": [],
                                "levels": [],
                            },
                        )
                        record["meanings"].append(korean)
                        record["partsOfSpeech"].append(part_of_speech)
                        record["levels"].append(level)

    records = []
    for record in records_by_key.values():
        record["meanings"] = unique(record["meanings"])[:MAX_MEANINGS]
        record["partsOfSpeech"] = clean_meta(record["partsOfSpeech"])
        record["levels"] = clean_meta(record["levels"])
        records.append(record)

    payload = {
        "source": {
            "name": "한국어기초사전 JSON",
            "url": "https://krdict.korean.go.kr/download/downloadPopup",
            "provider": "국립국어원",
        },
        "records": sorted(records, key=reading_sort_key),
    }
    TARGET.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {TARGET} with {len(records)} Japanese word entries.")


if __name__ == "__main__":
    main()
