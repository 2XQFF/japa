import gzip
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "kanjidic2.xml.gz"
JOYO_READINGS_SOURCE = ROOT / "data" / "joyo-readings.json"
HANJA_SOURCE = ROOT / "data" / "hanja.txt"
UNIHAN_VARIANTS_SOURCE = ROOT / "data" / "unihan" / "Unihan_Variants.txt"
KRDICT_SOURCE_DIR = ROOT / "data" / "krdict-json"
TARGET = ROOT / "data" / "kanji.json"
JOYO_GRADES = set(range(1, 9))
UNIHAN_MEANING_VARIANT_TYPES = {"kTraditionalVariant", "kSemanticVariant", "kZVariant"}
KRDICT_LEVEL_RANK = {"초급": 0, "중급": 1, "고급": 2}
KOREAN_FORM_OVERRIDES = {
    "内": ["內"],
    "呉": ["吳"],
    "姫": ["姬"],
    "娯": ["娛"],
    "尚": ["尙"],
    "悦": ["悅"],
    "惧": ["懼"],
    "戸": ["戶"],
    "教": ["敎"],
    "既": ["旣"],
    "歳": ["歲"],
    "没": ["沒"],
    "清": ["淸"],
    "税": ["稅"],
    "脱": ["脫"],
    "舎": ["舍"],
    "舗": ["舖"],
    "説": ["說"],
    "鋭": ["銳"],
    "閲": ["閱"],
    "闘": ["鬪"],
    "青": ["靑"],
    "飲": ["飮"],
}
KUN_GLOSS_OVERRIDES = {
    "下": {
        "した": ["아래"],
        "しも": ["아래쪽"],
        "もと": ["아래"],
        "さげる": ["내리다"],
        "さがる": ["내려가다"],
        "くだる": ["내려가다"],
        "くだす": ["내리다"],
        "くださる": ["주시다"],
        "おろす": ["내리다"],
        "おりる": ["내리다"],
    },
    "生": {
        "いきる": ["살다"],
        "いかす": ["살리다"],
        "いける": ["꽂다"],
        "うまれる": ["태어나다"],
        "うむ": ["낳다"],
        "おう": ["나다"],
        "はえる": ["나다"],
        "はやす": ["기르다"],
        "き": ["날것"],
        "なま": ["날것"],
    },
    "国": {
        "くに": ["나라"],
    },
    "上": {
        "うえ": ["위"],
        "うわ": ["위"],
        "かみ": ["위쪽"],
        "あげる": ["올리다"],
        "あがる": ["오르다"],
        "のぼる": ["오르다"],
        "のぼせる": ["올리다"],
        "のぼす": ["올리다"],
    },
    "行": {
        "いく": ["가다"],
        "ゆく": ["가다"],
        "おこなう": ["행하다"],
    },
}


def text(node, default=None):
    return node.text.strip() if node is not None and node.text else default


def all_text(parent, path):
    return [node.text.strip() for node in parent.findall(path) if node.text]


def unique(values):
    seen = set()
    out = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def is_cjk(char):
    code = ord(char)
    return (
        0x3400 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0x20000 <= code <= 0x2FA1F
    )


def normalize_reading(value):
    return value.replace(".", "").replace("-", "").strip()


def format_kun_reading(value):
    return value.replace(".", "-")


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def feature_value(node, key):
    for feature in as_list(node.get("feat") if isinstance(node, dict) else None):
        if isinstance(feature, dict) and feature.get("att") == key:
            return feature.get("val", "")
    return ""


def lemma_value(entry):
    for lemma in as_list(entry.get("Lemma") if isinstance(entry, dict) else None):
        if not isinstance(lemma, dict):
            continue
        feature = lemma.get("feat")
        if isinstance(feature, dict) and feature.get("att") == "writtenForm":
            return feature.get("val", "")
        for item in as_list(feature):
            if isinstance(item, dict) and item.get("att") == "writtenForm":
                return item.get("val", "")
    return ""


def split_hanja_info(value):
    return [
        item.strip()
        for item in value.replace(";", ",").split(",")
        if item.strip()
    ]


def load_hanja_meanings():
    if not HANJA_SOURCE.exists():
        raise SystemExit(f"Missing {HANJA_SOURCE}. Download hanja.txt first.")

    meanings = {}
    for line in HANJA_SOURCE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        _, literal, info = parts
        literal = literal.strip()
        if len(literal) != 1 or not is_cjk(literal):
            continue
        values = split_hanja_info(info)
        if values:
            meanings[literal] = unique(meanings.get(literal, []) + values)
    return meanings


def unihan_char(value):
    value = value.split("<", 1)[0]
    if not value.startswith("U+"):
        return None
    return chr(int(value[2:], 16))


def load_unihan_variants():
    if not UNIHAN_VARIANTS_SOURCE.exists():
        return {}

    variants = {}
    for line in UNIHAN_VARIANTS_SOURCE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3 or parts[1] not in UNIHAN_MEANING_VARIANT_TYPES:
            continue
        literal = unihan_char(parts[0])
        if not literal:
            continue
        values = [
            char
            for char in (unihan_char(item) for item in parts[2].split())
            if char and char != literal and is_cjk(char)
        ]
        if values:
            variants[literal] = unique(variants.get(literal, []) + values)
    return variants


def japanese_terms(value):
    terms = []
    for segment in re.split(r"[。;；]", value):
        segment = segment.strip()
        if not segment:
            continue
        match = re.match(r"(.+?)【(.+?)】", segment)
        if match:
            terms.append(match.group(1).strip())
            terms.extend(
                part.strip()
                for part in re.split(r"[・･,，、/／]", match.group(2))
                if part.strip()
            )
        else:
            terms.append(segment)
    return unique(terms)


def load_krdict_glosses(needed_terms):
    if not KRDICT_SOURCE_DIR.exists():
        return {}

    glosses = {}
    for path in KRDICT_SOURCE_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data["LexicalResource"]["Lexicon"]["LexicalEntry"]
        for entry in as_list(entries):
            korean = lemma_value(entry)
            if not korean:
                continue
            level = feature_value(entry, "vocabularyLevel")
            pos = feature_value(entry, "partOfSpeech")
            for sense in as_list(entry.get("Sense") if isinstance(entry, dict) else None):
                for equivalent in as_list(sense.get("Equivalent") if isinstance(sense, dict) else None):
                    if feature_value(equivalent, "language") != "일본어":
                        continue
                    for term in japanese_terms(feature_value(equivalent, "lemma")):
                        if term not in needed_terms:
                            continue
                        glosses.setdefault(term, []).append(
                            {
                                "text": korean,
                                "level": level,
                                "partOfSpeech": pos,
                            }
                        )
    return glosses


def korean_syllable(value):
    return bool(re.fullmatch(r"[가-힣]+", value))


def short_hanja_meanings(meanings):
    values = []
    for meaning in meanings:
        parts = meaning.split()
        if len(parts) > 1 and korean_syllable(parts[-1]):
            values.append(" ".join(parts[:-1]))
        else:
            values.append(meaning)
    return unique(values)


def hanja_sounds(meanings):
    sounds = []
    for meaning in meanings:
        parts = meaning.split()
        if parts and korean_syllable(parts[-1]):
            sounds.append(parts[-1])
    return set(sounds)


def meaning_roots(meanings):
    roots = set()
    for meaning in short_hanja_meanings(meanings):
        if not meaning:
            continue
        roots.add(meaning)
        if meaning.endswith("울"):
            roots.add(f"{meaning[:-1]}우")
    return roots


def choose_korean_glosses(candidates, record, limit=1):
    sounds = hanja_sounds(record.get("meanings", []))
    roots = meaning_roots(record.get("meanings", []))
    ranked = []
    for index, candidate in enumerate(candidates):
        text_value = candidate["text"].strip()
        if not text_value or "-" in text_value or " " in text_value or "[" in text_value:
            continue
        if text_value in sounds:
            continue
        semantic_rank = 0 if any(root in text_value or text_value in root for root in roots) else 1
        ranked.append(
            (
                semantic_rank,
                KRDICT_LEVEL_RANK.get(candidate.get("level", ""), 3),
                1 if candidate.get("partOfSpeech", "").startswith("보조") else 0,
                len(text_value),
                index,
                text_value,
            )
        )
    return unique(item[-1] for item in sorted(ranked))[:limit]


def korean_meanings_for(record, hanja_meanings, unihan_variants):
    lookup = [
        record["literal"],
        *record.get("oldForms", []),
        *record.get("variants", []),
        *unihan_variants.get(record["literal"], []),
    ]
    meanings = []
    for literal in lookup:
        meanings.extend(hanja_meanings.get(literal, []))
    return unique(meanings)


def old_forms_for(literal, traditional_forms):
    return unique([
        *traditional_forms.get(literal, []),
        *KOREAN_FORM_OVERRIDES.get(literal, []),
    ])


def display_kun_reading(literal, reading, examples):
    for example in examples:
        if literal not in example:
            continue
        after = example.split(literal, 1)[1]
        okurigana = ""
        for char in after:
            if "\u3041" <= char <= "\u3096":
                okurigana += char
            else:
                break
        if okurigana and reading.endswith(okurigana):
            return f"{reading[:-len(okurigana)]}-{okurigana}"
    return reading


def terms_for_kun(literal, examples):
    terms = []
    for example in examples:
        if literal not in example:
            continue
        term = re.split(r"[（(、，,。・･\s]", example, 1)[0]
        if term:
            terms.append(term)
    return unique(terms)


def official_kun_readings(literal, kun_details, krdict_glosses, record):
    readings = []
    for detail in kun_details.get(literal, []):
        raw = detail["reading"]
        override = KUN_GLOSS_OVERRIDES.get(literal, {}).get(raw)
        terms = terms_for_kun(literal, detail["examples"])
        glosses = override or unique(
            gloss
            for term in terms
            for gloss in choose_korean_glosses(krdict_glosses.get(term, []), record)
        )[:1]
        if not glosses:
            glosses = short_hanja_meanings(record.get("meanings", []))[:2]
        readings.append(
            {
                "text": display_kun_reading(literal, raw, detail["examples"]),
                "isJoyo": True,
                "glosses": glosses,
            }
        )
    return readings


def load_joyo_table():
    if not JOYO_READINGS_SOURCE.exists():
        raise SystemExit(f"Missing {JOYO_READINGS_SOURCE}. Download joyo-readings.json first.")

    data = json.loads(JOYO_READINGS_SOURCE.read_text(encoding="utf-8"))
    readings = {}
    traditional_forms = {}
    kun_details = {}
    for item in data:
        literal = item["漢字"]["通用字体"]
        on = set()
        kun = set()
        details = []
        for reading in item.get("音訓", []):
            value = normalize_reading(reading.get("読み", ""))
            if not value:
                continue
            if "\u30a0" <= value[0] <= "\u30ff":
                on.add(value)
            else:
                kun.add(value)
                details.append({"reading": value, "examples": reading.get("例", [])})
        readings[literal] = {"on": on, "kun": kun}
        kun_details[literal] = details
        traditional_forms[literal] = unique(
            char
            for char in item["漢字"].get("康熙字典体", "")
            if is_cjk(char) and char != literal
        )
    return readings, traditional_forms, kun_details


def mark_readings(values, official_values):
    official = {normalize_reading(value) for value in official_values}
    return [
        {"text": value, "isJoyo": normalize_reading(value) in official}
        for value in unique(values)
    ]


def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing {SOURCE}. Download kanjidic2.xml.gz first.")

    joyo_readings, traditional_forms, kun_details = load_joyo_table()
    hanja_meanings = load_hanja_meanings()
    unihan_variants = load_unihan_variants()
    needed_terms = {
        term
        for literal, details in kun_details.items()
        for detail in details
        for term in terms_for_kun(literal, detail["examples"])
    }
    krdict_glosses = load_krdict_glosses(needed_terms)

    with gzip.open(SOURCE, "rb") as fh:
        root = ET.parse(fh).getroot()

    characters = root.findall("character")
    jis_to_literal = {}
    ucs_to_literal = {}

    for char in characters:
        literal = text(char.find("literal"))
        for cp in char.findall("./codepoint/cp_value"):
            cp_type = cp.attrib.get("cp_type")
            value = text(cp)
            if cp_type in {"jis208", "jis212", "jis213"}:
                jis_to_literal[(cp_type, value)] = literal
            elif cp_type == "ucs":
                ucs_to_literal[value.lower()] = literal

    records = []

    for char in characters:
        literal = text(char.find("literal"))
        misc = char.find("misc")
        rmgroup = char.find("./reading_meaning/rmgroup")

        variants = []
        if misc is not None:
            for variant in misc.findall("variant"):
                var_type = variant.attrib.get("var_type")
                value = text(variant)
                variant_literal = None
                if var_type in {"jis208", "jis212", "jis213"}:
                    variant_literal = jis_to_literal.get((var_type, value))
                elif var_type == "ucs":
                    variant_literal = ucs_to_literal.get(value.lower())
                if variant_literal and variant_literal != literal:
                    variants.append(variant_literal)

        ja_on = []
        ja_kun = []
        if rmgroup is not None:
            ja_on = all_text(rmgroup, "./reading[@r_type='ja_on']")
            ja_kun = all_text(rmgroup, "./reading[@r_type='ja_kun']")

        official_readings = joyo_readings.get(literal, {"on": set(), "kun": set()})
        on_readings = mark_readings(ja_on, official_readings["on"])
        kun_readings = mark_readings([format_kun_reading(value) for value in ja_kun], official_readings["kun"])

        records.append(
            {
                "literal": literal,
                "unicode": f"U+{ord(literal):04X}",
                "strokes": [int(value) for value in all_text(misc, "stroke_count")] if misc is not None else [],
                "grade": int(text(misc.find("grade"), "0")) if misc is not None and misc.find("grade") is not None else None,
                "jlpt": int(text(misc.find("jlpt"), "0")) if misc is not None and misc.find("jlpt") is not None else None,
                "frequency": int(text(misc.find("freq"), "0")) if misc is not None and misc.find("freq") is not None else None,
                "on": [item["text"] for item in on_readings],
                "kun": [item["text"] for item in kun_readings],
                "onReadings": on_readings,
                "kunReadings": kun_readings,
                "meanings": [],
                "variants": unique(variants),
            }
        )

    joyo_records = [record for record in records if record.get("grade") in JOYO_GRADES]
    joyo_literals = {record["literal"] for record in joyo_records}

    old_to_new = {
        old: new
        for new in joyo_literals
        for old in old_forms_for(new, traditional_forms)
    }

    for record in joyo_records:
        old_forms = old_forms_for(record["literal"], traditional_forms)
        record["oldForms"] = old_forms
        record["variants"] = [
            variant
            for variant in record["variants"]
            if variant not in old_forms and variant != record["literal"]
        ]
        record["meanings"] = korean_meanings_for(record, hanja_meanings, unihan_variants)
        record["kunReadings"] = official_kun_readings(record["literal"], kun_details, krdict_glosses, record)
        record["kun"] = [item["text"] for item in record["kunReadings"]]

    payload = {
        "source": {
            "name": "KANJIDIC2",
            "url": "https://www.edrdg.org/kanjidic/kanjidic2.xml.gz",
            "license": "Creative Commons Attribution-ShareAlike 4.0",
            "copyright": "Electronic Dictionary Research and Development Group",
        },
        "joyoReadingsSource": {
            "name": "常用漢字表本表.json",
            "url": "https://github.com/mimneko/kanji-data/blob/main/%E5%B8%B8%E7%94%A8%E6%BC%A2%E5%AD%97%E8%A1%A8%E6%9C%AC%E8%A1%A8.json",
            "license": "CC0-1.0",
        },
        "hanjaMeaningsSource": {
            "name": "hanja.txt",
            "url": "https://github.com/libhangul/libhangul/blob/master/data/hanja/hanja.txt",
            "license": "BSD-style",
            "copyright": "Choe Hwanjin",
        },
        "unihanVariantsSource": {
            "name": "Unihan_Variants.txt",
            "url": "https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip",
            "license": "Unicode License v3",
            "optional": True,
        },
        "koreanJapaneseGlossSource": {
            "name": "한국어기초사전 JSON",
            "url": "https://krdict.korean.go.kr/download/downloadPopup",
            "provider": "국립국어원",
            "optional": True,
        },
        "oldToNew": dict(sorted(old_to_new.items())),
        "records": sorted(joyo_records, key=lambda item: item["literal"]),
    }

    TARGET.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {TARGET} with {len(joyo_records)} joyo kanji and {len(old_to_new)} old-form mappings.")


if __name__ == "__main__":
    main()
