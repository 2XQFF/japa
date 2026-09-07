import gzip
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "kanjidic2.xml.gz"
JOYO_READINGS_SOURCE = ROOT / "data" / "joyo-readings.json"
TARGET = ROOT / "data" / "kanji.json"
JOYO_GRADES = set(range(1, 9))


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


def load_joyo_table():
    if not JOYO_READINGS_SOURCE.exists():
        raise SystemExit(f"Missing {JOYO_READINGS_SOURCE}. Download joyo-readings.json first.")

    data = json.loads(JOYO_READINGS_SOURCE.read_text(encoding="utf-8"))
    readings = {}
    traditional_forms = {}
    for item in data:
        literal = item["漢字"]["通用字体"]
        on = set()
        kun = set()
        for reading in item.get("音訓", []):
            value = normalize_reading(reading.get("読み", ""))
            if not value:
                continue
            if "\u30a0" <= value[0] <= "\u30ff":
                on.add(value)
            else:
                kun.add(value)
        readings[literal] = {"on": on, "kun": kun}
        traditional_forms[literal] = unique(
            char
            for char in item["漢字"].get("康熙字典体", "")
            if is_cjk(char) and char != literal
        )
    return readings, traditional_forms


def mark_readings(values, official_values):
    official = {normalize_reading(value) for value in official_values}
    return [
        {"text": value, "isJoyo": normalize_reading(value) in official}
        for value in unique(values)
    ]


def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing {SOURCE}. Download kanjidic2.xml.gz first.")

    joyo_readings, traditional_forms = load_joyo_table()

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
        meanings = []
        if rmgroup is not None:
            ja_on = all_text(rmgroup, "./reading[@r_type='ja_on']")
            ja_kun = all_text(rmgroup, "./reading[@r_type='ja_kun']")
            meanings = [
                node.text.strip()
                for node in rmgroup.findall("meaning")
                if node.text and "m_lang" not in node.attrib
            ]

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
                "meanings": unique(meanings),
                "variants": unique(variants),
            }
        )

    joyo_records = [record for record in records if record.get("grade") in JOYO_GRADES]
    joyo_literals = {record["literal"] for record in joyo_records}

    old_to_new = {
        old: new
        for new, old_forms in traditional_forms.items()
        if new in joyo_literals
        for old in old_forms
    }

    for record in joyo_records:
        old_forms = traditional_forms.get(record["literal"], [])
        record["oldForms"] = old_forms
        record["variants"] = [
            variant
            for variant in record["variants"]
            if variant not in old_forms and variant != record["literal"]
        ]

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
        "oldToNew": dict(sorted(old_to_new.items())),
        "records": sorted(joyo_records, key=lambda item: item["literal"]),
    }

    TARGET.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {TARGET} with {len(joyo_records)} joyo kanji and {len(old_to_new)} old-form mappings.")


if __name__ == "__main__":
    main()
