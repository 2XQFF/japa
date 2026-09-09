import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "krdict-json"
TARGET_DIR = ROOT / "data" / "words"
META_TARGET = TARGET_DIR / "meta.json"
OLD_TARGET = ROOT / "data" / "words.json"
MAX_MEANINGS = 3
EMPTY_MARKERS = {"", "없음"}
COMMON_LEVELS = {"초급", "중급"}
LEVEL_RANKS = {"초급": 0, "중급": 1, "고급": 2}
GRAMMAR_ONLY_PARTS = {"어미", "조사", "접사", "의존 명사", "보조 동사", "보조 형용사", "품사 없음"}
PART_RANKS = {
    "명사": 0,
    "동사": 1,
    "형용사": 2,
    "부사": 3,
    "관형사": 4,
    "대명사": 5,
    "수사": 6,
    "감탄사": 7,
    "보조 동사": 8,
    "보조 형용사": 9,
    "의존 명사": 10,
    "접사": 11,
    "조사": 12,
    "어미": 13,
    "품사 없음": 99,
}
INVALID_WORD_PATTERN = re.compile(r"[#…()[\]{}<>「」『』【】（）]")
ALLOWED_TERM_PATTERN = re.compile(r"^[A-Za-z0-9\u3040-\u30ff\u3400-\u9fff\uff10-\uff5a々〆ヶー・･]+$")
PHRASE_MARKER_PATTERN = re.compile(r"(を|にも|では|とは|から|まで|より|している|してある|になる|にする|が良い|が悪い|がある|がない)")


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


def kana_fold(value):
    return "".join(
        chr(ord(char) + 0x60) if "\u3041" <= char <= "\u3096" else char
        for char in value
    )


def clean_search_value(value):
    value = kana_fold(value.lower())
    return re.sub(r"[.\-\s・･,，、/／]", "", value)


def bucket_key(value):
    value = clean_search_value(value)
    return value[0] if value else ""


def bucket_filename(key):
    return f"u{ord(key):x}.json" if key else "empty.json"


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


def level_rank(value):
    return LEVEL_RANKS.get(value, 9)


def best_level_rank(record):
    ranks = [level_rank(level) for level in record["levels"]]
    return min(ranks) if ranks else 8


def part_sort_key(value):
    return (PART_RANKS.get(value, 50), value)


def meaning_sort_key(record, meaning):
    rank = record["meaningRanks"].get(meaning, 9)
    has_affix_mark = meaning.startswith("-") or meaning.endswith("-")
    has_space = " " in meaning
    mixed = not re.fullmatch(r"[가-힣-]+", meaning)
    return (rank, has_affix_mark, has_space, mixed, len(meaning), meaning)


def record_sort_key(record):
    reading = clean_search_value(record["reading"] or record["term"])
    return (
        reading,
        best_level_rank(record),
        len(record["term"]),
        record["term"],
    )


def clean_meta(values):
    return [value for value in unique(values) if value not in EMPTY_MARKERS]


def clean_parts(values):
    values = clean_meta(values)
    if len(values) > 1 and "품사 없음" in values:
        values.remove("품사 없음")
    return sorted(values, key=part_sort_key)


def clean_levels(values):
    return sorted(clean_meta(values), key=lambda value: (level_rank(value), value))


def compact_record(record):
    return [
        record["term"],
        record["reading"],
        record["meanings"],
        record["partsOfSpeech"],
        record["levels"],
    ]


def has_common_level(record):
    return any(level in COMMON_LEVELS for level in record["levels"])


def has_usable_level(record):
    return has_common_level(record) or (
        not record["levels"]
        and bool(record["reading"])
        and len(record["term"]) <= 12
    )


def has_dictionary_part(record):
    return any(part not in GRAMMAR_ONLY_PARTS for part in record["partsOfSpeech"])


def is_single_han_term(term):
    return bool(re.fullmatch(r"[\u3400-\u9fff]", term))


def is_clean_word_form(value):
    if not value or len(value) > 24:
        return False
    if INVALID_WORD_PATTERN.search(value) or re.search(r"\s", value):
        return False
    if PHRASE_MARKER_PATTERN.search(value):
        return False
    return bool(ALLOWED_TERM_PATTERN.fullmatch(value))


def is_usable_record(record):
    return (
        has_usable_level(record)
        and has_dictionary_part(record)
        and is_clean_word_form(record["term"])
        and (not record["reading"] or is_clean_word_form(record["reading"]))
        and not is_single_han_term(record["term"])
    )


def bucket_keys(record):
    return unique(
        [
            bucket_key(record["term"]),
            bucket_key(record["reading"]),
            *(bucket_key(meaning) for meaning in record["meanings"]),
        ]
    )


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
                                "meaningRanks": {},
                                "partsOfSpeech": [],
                                "levels": [],
                            },
                        )
                        record["meanings"].append(korean)
                        current_rank = record["meaningRanks"].get(korean, 9)
                        record["meaningRanks"][korean] = min(current_rank, level_rank(level))
                        record["partsOfSpeech"].append(part_of_speech)
                        record["levels"].append(level)

    records = []
    for record in records_by_key.values():
        record["meanings"] = sorted(unique(record["meanings"]), key=lambda meaning: meaning_sort_key(record, meaning))[:MAX_MEANINGS]
        record["partsOfSpeech"] = clean_parts(record["partsOfSpeech"])
        record["levels"] = clean_levels(record["levels"])
        if is_usable_record(record):
            records.append(record)

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for path in TARGET_DIR.glob("*.json"):
        path.unlink()
    if OLD_TARGET.exists():
        OLD_TARGET.unlink()

    buckets = {}
    for record in sorted(records, key=record_sort_key):
        compact = compact_record(record)
        for key in bucket_keys(record):
            if key:
                buckets.setdefault(key, []).append(compact)

    for key, bucket_records in sorted(buckets.items()):
        filename = bucket_filename(key)
        (TARGET_DIR / filename).write_text(
            json.dumps(bucket_records, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    payload = {
        "source": {
            "name": "한국어기초사전 JSON",
            "url": "https://krdict.korean.go.kr/download/downloadPopup",
            "provider": "국립국어원",
        },
        "schema": ["term", "reading", "meanings", "partsOfSpeech", "levels"],
        "count": len(records),
    }
    META_TARGET.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {TARGET_DIR} with {len(records)} Japanese word entries in {len(buckets)} buckets.")


if __name__ == "__main__":
    main()
