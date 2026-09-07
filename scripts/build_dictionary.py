import gzip
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "kanjidic2.xml.gz"
TARGET = ROOT / "data" / "kanji.json"


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


def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing {SOURCE}. Download kanjidic2.xml.gz first.")

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
    variant_pairs = set()

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
                    variant_pairs.add(tuple(sorted((literal, variant_literal))))

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

        records.append(
            {
                "literal": literal,
                "unicode": f"U+{ord(literal):04X}",
                "strokes": [int(value) for value in all_text(misc, "stroke_count")] if misc is not None else [],
                "grade": int(text(misc.find("grade"), "0")) if misc is not None and misc.find("grade") is not None else None,
                "jlpt": int(text(misc.find("jlpt"), "0")) if misc is not None and misc.find("jlpt") is not None else None,
                "frequency": int(text(misc.find("freq"), "0")) if misc is not None and misc.find("freq") is not None else None,
                "on": unique(ja_on),
                "kun": unique(ja_kun),
                "meanings": unique(meanings),
                "variants": unique(variants),
            }
        )

    by_literal = {record["literal"]: record for record in records}

    def modern_score(record):
        score = 0
        grade = record.get("grade")
        if grade is not None and grade < 10:
            score += 1000 - grade
        if record.get("frequency") is not None:
            score += 400
        if record.get("jlpt") is not None:
            score += 200
        if grade == 10:
            score -= 100
        return score

    old_to_new = {}
    for left, right in variant_pairs:
        left_record = by_literal[left]
        right_record = by_literal[right]
        if modern_score(left_record) == modern_score(right_record):
            continue
        old, new = (right, left) if modern_score(left_record) > modern_score(right_record) else (left, right)
        old_to_new[old] = new

    for record in records:
        record["oldForms"] = sorted([old for old, new in old_to_new.items() if new == record["literal"]])

    payload = {
        "source": {
            "name": "KANJIDIC2",
            "url": "https://www.edrdg.org/kanjidic/kanjidic2.xml.gz",
            "license": "Creative Commons Attribution-ShareAlike 4.0",
            "copyright": "Electronic Dictionary Research and Development Group",
        },
        "oldToNew": dict(sorted(old_to_new.items())),
        "records": sorted(records, key=lambda item: item["literal"]),
    }

    TARGET.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {TARGET} with {len(records)} kanji and {len(old_to_new)} old-form mappings.")


if __name__ == "__main__":
    main()
