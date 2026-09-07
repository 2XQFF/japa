# 일본어용 한자사전

일본 상용한자만 대상으로 하는 정적 웹 사전입니다. 구자체로 검색하면 대응하는 신자체 항목을 자동으로 보여주고, 신자체 항목에서는 음독과 훈독을 함께 확인할 수 있습니다. 구자체 칸에는 상용한자표의 강희자전체, 즉 한국 정체자에 가까운 전통 자형을 넣고, 그 밖의 자형은 이체자 칸에 따로 표시합니다. 상용표 밖 독음은 별도 색으로 표시합니다.

## 실행

```powershell
python -m http.server 8000
```

브라우저에서 `http://localhost:8000`을 엽니다.

## 데이터 갱신

```powershell
Invoke-WebRequest -Uri "https://www.edrdg.org/kanjidic/kanjidic2.xml.gz" -OutFile "data\kanjidic2.xml.gz"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/mimneko/kanji-data/main/%E5%B8%B8%E7%94%A8%E6%BC%A2%E5%AD%97%E8%A1%A8%E6%9C%AC%E8%A1%A8.json" -OutFile "data\joyo-readings.json"
python scripts\build_dictionary.py
```

한자 데이터는 EDRDG의 KANJIDIC2를 사용합니다. 상용독음 판별에는 문화청 상용한자표 본표를 바탕으로 정리된 `mimneko/kanji-data`의 `常用漢字表本表.json`을 사용합니다.
