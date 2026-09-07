# 일본어용 한자사전

구자체로 검색하면 대응하는 신자체 항목을 자동으로 보여주고, 신자체 항목에서는 음독과 훈독을 함께 확인할 수 있는 정적 웹 사전입니다.

## 실행

```powershell
python -m http.server 8000
```

브라우저에서 `http://localhost:8000`을 엽니다.

## 데이터 갱신

```powershell
Invoke-WebRequest -Uri "https://www.edrdg.org/kanjidic/kanjidic2.xml.gz" -OutFile "data\kanjidic2.xml.gz"
python scripts\build_dictionary.py
```

데이터는 EDRDG의 KANJIDIC2를 사용합니다. KANJIDIC2는 Creative Commons Attribution-ShareAlike 4.0 조건으로 제공됩니다.
