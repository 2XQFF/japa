import html
import json
import re
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "krdict-json"
JMDICT_SOURCE = ROOT / "data" / "JMdict_e.gz"
TARGET_DIR = ROOT / "data" / "words"
META_TARGET = TARGET_DIR / "meta.json"
OLD_TARGET = ROOT / "data" / "words.json"
MAX_MEANINGS = 1
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
CANONICAL_MEANINGS = {
    "する": ["하다"],
    "為る:する": ["하다"],
    "なる": ["되다"],
    "成る": ["되다"],
    "できる": ["되다"],
    "出来る": ["되다"],
    "ある": ["있다"],
    "有る": ["있다"],
    "いる": ["있다"],
    "居る": ["있다"],
    "ない": ["없다"],
    "無い": ["없다"],
    "いい": ["좋다"],
    "良い": ["좋다"],
    "悪い": ["나쁘다"],
    "好きだ": ["좋아하다"],
    "嫌いだ": ["싫다"],
    "少ない": ["적다"],
    "古い": ["낡다"],
    "熱い": ["뜨겁다"],
    "冷たい": ["차갑다"],
    "狭い": ["좁다"],
    "易しい": ["쉽다"],
    "面白い": ["재미있다"],
    "上がる": ["오르다"],
    "上げる": ["올리다"],
    "上る": ["오르다"],
    "下がる": ["내려가다"],
    "下げる": ["내리다"],
    "下る": ["내려가다"],
    "下ろす": ["내리다"],
    "入る": ["들어가다"],
    "入れる": ["넣다"],
    "出る": ["나오다"],
    "出す": ["내다"],
    "行く": ["가다"],
    "いく": ["가다"],
    "来る": ["오다"],
    "くる": ["오다"],
    "見る": ["보다"],
    "みる": ["보다"],
    "聞く": ["듣다"],
    "読む": ["읽다"],
    "書く": ["쓰다"],
    "食べる": ["먹다"],
    "飲む": ["마시다"],
    "寝る": ["자다"],
    "起きる": ["일어나다"],
    "買う": ["사다"],
    "売る": ["팔다"],
    "待つ": ["기다리다"],
    "使う": ["쓰다"],
    "作る": ["만들다"],
    "取る": ["잡다"],
    "持つ": ["가지다"],
    "思う": ["생각하다"],
    "言う": ["말하다"],
    "いう": ["말하다"],
    "分かる": ["알다"],
    "わかる": ["알다"],
    "知る": ["알다"],
    "話す": ["말하다"],
    "鳴る": ["울다"],
    "会う": ["만나다"],
    "帰る": ["돌아가다"],
    "歩く": ["걷다"],
    "走る": ["달리다"],
    "泳ぐ": ["헤엄치다"],
    "休む": ["쉬다"],
    "働く": ["일하다"],
    "勉強する": ["공부하다"],
    "教える": ["가르치다"],
    "習う": ["배우다"],
    "忘れる": ["잊다"],
    "覚える": ["기억하다"],
    "死ぬ": ["죽다"],
    "生まれる": ["태어나다"],
    "住む": ["살다"],
    "乗る": ["타다"],
    "降りる": ["내리다"],
    "着る": ["입다"],
    "履く": ["신다"],
    "脱ぐ": ["벗다"],
    "洗う": ["씻다"],
    "磨く": ["닦다"],
    "切る": ["자르다"],
    "貸す": ["빌려주다"],
    "借りる": ["빌리다"],
    "返す": ["돌려주다"],
    "送る": ["보내다"],
    "開ける": ["열다"],
    "開く": ["열리다"],
    "閉める": ["닫다"],
    "閉まる": ["닫히다"],
    "立つ": ["서다"],
    "座る": ["앉다"],
    "暗い": ["어둡다"],
    "明るい": ["밝다"],
    "近い": ["가깝다"],
    "遠い": ["멀다"],
    "強い": ["강하다"],
    "弱い": ["약하다"],
    "太い": ["굵다"],
    "細い": ["가늘다"],
    "重い": ["무겁다"],
    "軽い": ["가볍다"],
    "甘い": ["달다"],
    "辛い:からい": ["맵다"],
    "辛い:つらい": ["괴롭다"],
}
CANONICAL_WORD_CLASSES = {
    "する": ["변칙동사"],
    "為る:する": ["변칙동사"],
    "来る": ["변칙동사"],
    "くる": ["변칙동사"],
    "好きだ": ["형용동사"],
    "嫌いだ": ["형용동사"],
}
WORD_CLASS_RANKS = {
    "5단동사": 0,
    "1단동사": 1,
    "변칙동사": 2,
    "い형용사": 3,
    "형용동사": 4,
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
    count = record["meaningCounts"].get(meaning, 0)
    has_affix_mark = meaning.startswith("-") or meaning.endswith("-")
    has_space = " " in meaning
    mixed = not re.fullmatch(r"[가-힣-]+", meaning)
    return (rank, has_affix_mark, has_space, mixed, -count, len(meaning), meaning)


def word_class_sort_key(value):
    return (WORD_CLASS_RANKS.get(value, 99), value)


def record_sort_key(record):
    reading = clean_search_value(record["reading"] or record["term"])
    return (
        record["frequencyRank"],
        -record["sourceCount"],
        best_level_rank(record),
        len(record["term"]),
        reading,
        record["term"],
    )


def duplicate_record_sort_key(record):
    reading = record["reading"]
    clean_reading = clean_search_value(reading or record["term"])
    return (
        record["frequencyRank"],
        "・" in reading or "･" in reading,
        -record["sourceCount"],
        best_level_rank(record),
        len(clean_reading),
        clean_reading,
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


def primary_reading(value):
    return re.split(r"[・･]", value, 1)[0] if value else ""


def canonical_meanings(record):
    term = record["term"]
    reading = primary_reading(record["reading"])
    keys = [
        f"{term}:{reading}" if reading else "",
        term,
        clean_search_value(term),
    ]
    existing = set(record["meanings"])
    for key in keys:
        values = CANONICAL_MEANINGS.get(key)
        if values:
            return [value for value in values if value in existing] or values
    return []


def priority_rank(values):
    best = 9000
    for value in values:
        if not value:
            continue
        if value.startswith("nf") and value[2:].isdigit():
            best = min(best, int(value[2:]))
        elif value == "ichi1":
            best = min(best, 60)
        elif value == "news1":
            best = min(best, 80)
        elif value == "spec1":
            best = min(best, 100)
        elif value == "gai1":
            best = min(best, 120)
        elif value == "ichi2":
            best = min(best, 160)
        elif value == "news2":
            best = min(best, 180)
        elif value == "spec2":
            best = min(best, 200)
        elif value == "gai2":
            best = min(best, 220)
    return best


def classes_from_jmdict_pos(values):
    classes = []
    text = " ".join(values)
    if "Godan verb" in text:
        classes.append("5단동사")
    if "Ichidan verb" in text:
        classes.append("1단동사")
    if "suru verb" in text or "Kuru verb" in text or "irregular nu verb" in text:
        classes.append("변칙동사")
    if "adjective (keiyoushi)" in text:
        classes.append("い형용사")
    if "adjectival nouns or quasi-adjectives" in text:
        classes.append("형용동사")
    return sorted(unique(classes), key=word_class_sort_key)


def merge_jmdict_feature(features, key, priorities, positions):
    if not key:
        return
    feature = features.setdefault(key, {"frequencyRank": 9000, "classes": []})
    feature["frequencyRank"] = min(feature["frequencyRank"], priority_rank(priorities))
    feature["classes"] = unique(feature["classes"] + classes_from_jmdict_pos(positions))


def load_jmdict_features():
    features = {}
    if not JMDICT_SOURCE.exists():
        return features

    with gzip.open(JMDICT_SOURCE, "rt", encoding="utf-8") as source:
        for _event, elem in ET.iterparse(source, events=("end",)):
            if elem.tag != "entry":
                continue

            kanji_forms = [item.text for item in elem.findall("./k_ele/keb") if item.text]
            reading_forms = [item.text for item in elem.findall("./r_ele/reb") if item.text]
            priorities = [
                item.text
                for item in elem.findall("./k_ele/ke_pri") + elem.findall("./r_ele/re_pri")
                if item.text
            ]
            positions = [item.text for item in elem.findall("./sense/pos") if item.text]

            for term in kanji_forms:
                merge_jmdict_feature(features, f"{term}\t", priorities, positions)
                for reading in reading_forms:
                    merge_jmdict_feature(features, f"{term}\t{reading}", priorities, positions)
            for reading in reading_forms:
                merge_jmdict_feature(features, f"{reading}\t", priorities, positions)

            elem.clear()
    return features


def record_jmdict_keys(record):
    term = record["term"]
    reading = primary_reading(record["reading"])
    keys = [
        f"{term}\t{reading}" if reading else "",
        f"{term}\t",
    ]
    if term.endswith("だ"):
        base = term[:-1]
        base_reading = reading[:-1] if reading.endswith("だ") else reading
        keys.extend(
            [
                f"{base}\t{base_reading}" if base_reading else "",
                f"{base}\t",
            ]
        )
    return [key for key in keys if key]


def canonical_word_classes(record):
    term = record["term"]
    reading = primary_reading(record["reading"])
    keys = [
        f"{term}:{reading}" if reading else "",
        term,
        clean_search_value(term),
    ]
    for key in keys:
        values = CANONICAL_WORD_CLASSES.get(key)
        if values:
            return values
    return []


def apply_jmdict_features(record, features):
    classes = canonical_word_classes(record)
    frequency_rank = 9000
    for key in record_jmdict_keys(record):
        feature = features.get(key)
        if not feature:
            continue
        frequency_rank = min(frequency_rank, feature["frequencyRank"])
        if not classes:
            classes = unique(classes + feature["classes"])
    record["wordClasses"] = sorted(classes, key=word_class_sort_key)
    record["frequencyRank"] = frequency_rank


def merge_duplicate_record_group(group):
    merged = dict(sorted(group, key=duplicate_record_sort_key)[0])
    merged["partsOfSpeech"] = clean_parts(
        part
        for record in group
        for part in record["partsOfSpeech"]
    )
    merged["levels"] = clean_levels(
        level
        for record in group
        for level in record["levels"]
    )
    merged["wordClasses"] = sorted(
        unique(
            word_class
            for record in group
            for word_class in record["wordClasses"]
        ),
        key=word_class_sort_key,
    )
    merged["frequencyRank"] = min(record["frequencyRank"] for record in group)
    merged["sourceCount"] = sum(record["sourceCount"] for record in group)
    return merged


def dedupe_records(records):
    groups = {}
    for record in records:
        key = (record["term"], tuple(record["meanings"]))
        groups.setdefault(key, []).append(record)
    return [merge_duplicate_record_group(group) for group in groups.values()]


def compact_record(record):
    return [
        record["term"],
        record["reading"],
        record["meanings"],
        record["partsOfSpeech"],
        record["levels"],
        record["wordClasses"],
        record["frequencyRank"],
        record["sourceCount"],
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

    jmdict_features = load_jmdict_features()
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
                                "meaningCounts": {},
                                "partsOfSpeech": [],
                                "levels": [],
                                "wordClasses": [],
                                "frequencyRank": 9000,
                                "sourceCount": 0,
                            },
                        )
                        record["meanings"].append(korean)
                        record["sourceCount"] += 1
                        record["meaningCounts"][korean] = record["meaningCounts"].get(korean, 0) + 1
                        current_rank = record["meaningRanks"].get(korean, 9)
                        record["meaningRanks"][korean] = min(current_rank, level_rank(level))
                        record["partsOfSpeech"].append(part_of_speech)
                        record["levels"].append(level)

    records = []
    for record in records_by_key.values():
        canonical = canonical_meanings(record)
        record["meanings"] = canonical or sorted(unique(record["meanings"]), key=lambda meaning: meaning_sort_key(record, meaning))[:MAX_MEANINGS]
        record["partsOfSpeech"] = clean_parts(record["partsOfSpeech"])
        record["levels"] = clean_levels(record["levels"])
        apply_jmdict_features(record, jmdict_features)
        if is_usable_record(record):
            records.append(record)
    records = dedupe_records(records)

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
        "jmdictSource": {
            "name": "JMdict",
            "url": "https://www.edrdg.org/jmdict/j_jmdict.html",
            "optional": True,
        },
        "schema": ["term", "reading", "meanings", "partsOfSpeech", "levels", "wordClasses", "frequencyRank", "sourceCount"],
        "count": len(records),
    }
    META_TARGET.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {TARGET_DIR} with {len(records)} Japanese word entries in {len(buckets)} buckets.")


if __name__ == "__main__":
    main()
