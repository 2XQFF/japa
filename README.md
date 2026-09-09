# 일본어 사전

일본 상용한자 사전과 오프라인 일본어 단어사전을 함께 제공하는 정적 웹 사전입니다. 한자사전과 단어사전은 별도 HTML/JS로 분리되어 필요한 데이터만 읽습니다. 구자체로 검색하면 대응하는 신자체 항목을 자동으로 보여주고, 신자체 항목에서는 음독과 훈독을 함께 확인할 수 있습니다. 구자체 칸에는 상용한자표의 강희자전체, 즉 한국 정체자에 가까운 전통 자형을 넣고, 그 밖의 자형은 이체자 칸에 따로 표시합니다. 훈독의 어간/어미 경계는 하이픈으로 표시하고, 상용표 밖 독음은 별도 색으로 표시합니다.
뜻은 영어 gloss 대신 한국 한자 훈음으로 표시합니다.
단어사전은 `words.html`에서 열리며, 첫 화면에서는 `data/words/meta.json`만 읽고 검색어 첫 글자에 해당하는 `data/words/*.json` 조각 파일만 추가로 불러옵니다.

## 실행

```powershell
python -m http.server 8000
```

브라우저에서 `http://localhost:8000`을 엽니다.

## 데이터 갱신

```powershell
Invoke-WebRequest -Uri "https://www.edrdg.org/kanjidic/kanjidic2.xml.gz" -OutFile "data\kanjidic2.xml.gz"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/mimneko/kanji-data/main/%E5%B8%B8%E7%94%A8%E6%BC%A2%E5%AD%97%E8%A1%A8%E6%9C%AC%E8%A1%A8.json" -OutFile "data\joyo-readings.json"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/libhangul/libhangul/master/data/hanja/hanja.txt" -OutFile "data\hanja.txt"
Invoke-WebRequest -Uri "https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip" -OutFile "data\Unihan.zip"
Expand-Archive -LiteralPath "data\Unihan.zip" -DestinationPath "data\unihan" -Force
Invoke-WebRequest -Uri "https://krdict.korean.go.kr/dicBatchDownload?seq=214" -OutFile "data\krdict-json.zip"
Expand-Archive -LiteralPath "data\krdict-json.zip" -DestinationPath "data\krdict-json" -Force
python scripts\build_dictionary.py
python scripts\build_words_dictionary.py
```

한자 데이터는 EDRDG의 KANJIDIC2를 사용합니다. 상용독음 판별에는 문화청 상용한자표 본표를 바탕으로 정리된 `mimneko/kanji-data`의 `常用漢字表本表.json`을 사용합니다. 한국어 훈음은 libhangul의 `hanja.txt`를 사용하고, 훈음 보조 조회와 단어사전에는 Unicode `Unihan_Variants.txt`와 국립국어원 한국어기초사전 JSON을 사용합니다.
