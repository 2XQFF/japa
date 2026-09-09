const state = {
  dictionary: "kanji",
  mode: "auto",
  records: [],
  words: [],
  wordStatus: "idle",
  byLiteral: new Map(),
  oldToNew: new Map(),
};

const WORD_TERM = 0;
const WORD_READING = 1;
const WORD_MEANINGS = 2;
const WORD_PARTS = 3;
const WORD_LEVELS = 4;

const els = {
  query: document.querySelector("#query"),
  status: document.querySelector("#status"),
  results: document.querySelector("#results"),
  template: document.querySelector("#card-template"),
  wordTemplate: document.querySelector("#word-card-template"),
  filters: document.querySelectorAll("[data-mode]"),
  filterBox: document.querySelector(".filters"),
  dictionaryTabs: document.querySelectorAll("[data-dictionary]"),
};

function kanaFold(value) {
  return value.replace(/[\u3041-\u3096]/g, (char) =>
    String.fromCharCode(char.charCodeAt(0) + 0x60)
  );
}

function cleanReading(value) {
  return kanaFold(value.replace(/[.\-\s]/g, ""));
}

function cleanWord(value) {
  return cleanReading(value.toLowerCase().replace(/[・･,，、/／]/g, ""));
}

function wordTerm(record) {
  return record[WORD_TERM] || "";
}

function wordReading(record) {
  return record[WORD_READING] || "";
}

function wordMeanings(record) {
  return record[WORD_MEANINGS] || [];
}

function wordParts(record) {
  return record[WORD_PARTS] || [];
}

function wordLevels(record) {
  return record[WORD_LEVELS] || [];
}

function labelList(values, empty = "자료 없음") {
  return values && values.length ? values.join(" · ") : empty;
}

function readingItems(record, richKey, plainKey) {
  if (record[richKey]) return record[richKey];
  return record[plainKey].map((text) => ({ text, isJoyo: true }));
}

function readingLabel(reading) {
  if (!reading.glosses || !reading.glosses.length) return reading.text;
  return `${reading.text}(${reading.glosses.join("/")})`;
}

function buildSearchText(record) {
  return [
    record.literal,
    ...record.oldForms,
    ...record.variants,
    ...record.on,
    ...record.kun,
    ...record.meanings,
    ...readingItems(record, "kunReadings", "kun").flatMap((reading) => reading.glosses || []),
  ]
    .join(" ")
    .toLowerCase();
}

function buildWordSearchText(record) {
  return [wordTerm(record), wordReading(record), ...wordMeanings(record), ...wordParts(record), ...wordLevels(record)]
    .join(" ")
    .toLowerCase();
}

function findKanjiMatches(rawQuery) {
  const query = rawQuery.trim();
  if (!query) return [];

  const literalHits = new Map();
  for (const char of [...query]) {
    const modern = state.oldToNew.get(char);
    if (modern && state.byLiteral.has(modern)) {
      literalHits.set(modern, { record: state.byLiteral.get(modern), redirectedFrom: char });
    } else if (state.byLiteral.has(char)) {
      literalHits.set(char, { record: state.byLiteral.get(char), redirectedFrom: null });
    }
  }

  if (state.mode === "kanji") {
    return [...literalHits.values()];
  }

  if (literalHits.size && [...query].every((char) => /\p{Script=Han}/u.test(char))) {
    return [...literalHits.values()];
  }

  const foldedQuery = cleanReading(query.toLowerCase());
  const generalHits =
    state.mode === "auto" || state.mode === "reading"
      ? state.records
          .filter((record) => {
            if (literalHits.has(record.literal)) return false;
            const readingText = cleanReading([...record.on, ...record.kun].join(" ").toLowerCase());
            if (state.mode === "reading") return readingText.includes(foldedQuery);
            return buildSearchText(record).includes(query.toLowerCase()) || readingText.includes(foldedQuery);
          })
          .slice(0, 80)
          .map((record) => ({ record, redirectedFrom: null }))
      : [];

  return [...literalHits.values(), ...generalHits].slice(0, 100);
}

function wordScore(record, query, foldedQuery) {
  const term = wordTerm(record).toLowerCase();
  const reading = wordReading(record).toLowerCase();
  const foldedTerm = cleanWord(wordTerm(record));
  const foldedReading = cleanWord(wordReading(record));
  const meanings = wordMeanings(record).join(" ").toLowerCase();
  const searchText = buildWordSearchText(record);

  if (term === query || reading === query) return 0;
  if (foldedTerm === foldedQuery || foldedReading === foldedQuery) return 1;
  if (term.startsWith(query) || reading.startsWith(query)) return 2;
  if (foldedTerm.startsWith(foldedQuery) || foldedReading.startsWith(foldedQuery)) return 3;
  if (term.includes(query) || reading.includes(query)) return 4;
  if (foldedTerm.includes(foldedQuery) || foldedReading.includes(foldedQuery)) return 5;
  if (meanings.includes(query)) return 6;
  if (searchText.includes(query)) return 7;
  return null;
}

function findWordMatches(rawQuery) {
  const query = rawQuery.trim().toLowerCase();
  if (!query) return [];

  const foldedQuery = cleanWord(query);
  return state.words
    .map((record) => ({ record, score: wordScore(record, query, foldedQuery) }))
    .filter((hit) => hit.score !== null)
    .sort((a, b) => a.score - b.score || wordTerm(a.record).length - wordTerm(b.record).length || wordTerm(a.record).localeCompare(wordTerm(b.record), "ja"))
    .slice(0, 100);
}

function renderCard(hit) {
  const node = els.template.content.firstElementChild.cloneNode(true);
  const { record, redirectedFrom } = hit;
  node.querySelector(".literal").textContent = record.literal;
  node.querySelector(".meta").textContent = [
    record.unicode,
    record.strokes.length ? `${record.strokes[0]}획` : null,
    record.grade ? `학년 ${record.grade}` : null,
    record.jlpt ? `JLPT ${record.jlpt}` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  const notice = node.querySelector(".notice");
  if (redirectedFrom) {
    notice.textContent = `구자체 ${redirectedFrom} 검색 결과: 신자체 ${record.literal} 항목을 함께 표시합니다.`;
    notice.classList.remove("hidden");
  }

  renderReadingList(node.querySelector(".on"), readingItems(record, "onReadings", "on"));
  renderReadingList(node.querySelector(".kun"), readingItems(record, "kunReadings", "kun"));
  node.querySelector(".old").textContent = labelList(record.oldForms);
  node.querySelector(".variants").textContent = labelList(record.variants);
  node.querySelector(".meanings").textContent = labelList(record.meanings);
  return node;
}

function hasKanji(value) {
  return /\p{Script=Han}/u.test(value);
}

function isKanji(value) {
  return /^\p{Script=Han}+$/u.test(value);
}

function primaryReading(value) {
  return value.split(/[・･]/, 1)[0] || value;
}

function createRubyForTerm(term, reading) {
  const fragment = document.createDocumentFragment();
  const kana = primaryReading(reading || "");
  if (!term || !kana || !hasKanji(term)) {
    fragment.append(document.createTextNode(term));
    return fragment;
  }

  const tokens = term.match(/\p{Script=Han}+|[^\p{Script=Han}]+/gu) || [term];
  let readingIndex = 0;
  tokens.forEach((token, index) => {
    if (!isKanji(token)) {
      fragment.append(document.createTextNode(token));
      if (kana.startsWith(token, readingIndex)) readingIndex += token.length;
      return;
    }

    const nextKana = tokens.slice(index + 1).find((item) => !isKanji(item) && /[\u3041-\u3096\u30a1-\u30fa]/.test(item));
    const nextIndex = nextKana ? kana.indexOf(nextKana, readingIndex) : -1;
    const rubyText = nextIndex >= readingIndex ? kana.slice(readingIndex, nextIndex) : kana.slice(readingIndex);
    if (rubyText) readingIndex += rubyText.length;

    const ruby = document.createElement("ruby");
    ruby.append(document.createTextNode(token));
    const rt = document.createElement("rt");
    rt.textContent = rubyText || kana;
    ruby.append(rt);
    fragment.append(ruby);
  });
  return fragment;
}

function renderWordCard(hit) {
  const node = els.wordTemplate.content.firstElementChild.cloneNode(true);
  const { record } = hit;
  const term = wordTerm(record);
  const readingValue = wordReading(record);
  const termNode = node.querySelector(".word-term");
  termNode.replaceChildren(createRubyForTerm(term, readingValue));

  const reading = node.querySelector(".word-reading");
  if (readingValue && readingValue !== term && (!hasKanji(term) || /[・･]/.test(readingValue))) {
    reading.textContent = readingValue;
  } else {
    reading.classList.add("hidden");
  }

  node.querySelector(".word-meanings").textContent = labelList(wordMeanings(record));
  node.querySelector(".word-pos").textContent = labelList(wordParts(record));
  node.querySelector(".word-levels").textContent = labelList(wordLevels(record));
  return node;
}

function renderReadingList(target, readings) {
  if (!readings.length) {
    target.textContent = "자료 없음";
    return;
  }

  const nodes = [];
  readings.forEach((reading, index) => {
    if (index) nodes.push(document.createTextNode(" · "));
    const span = document.createElement("span");
    span.className = reading.isJoyo ? "reading-item" : "reading-item non-joyo";
    span.textContent = readingLabel(reading);
    if (!reading.isJoyo) span.title = "상용표 밖 독음";
    nodes.push(span);
  });
  target.replaceChildren(...nodes);
}

function render() {
  if (state.dictionary === "words" && state.wordStatus !== "ready") {
    els.results.replaceChildren();
    els.status.textContent = state.wordStatus === "error" ? "단어 데이터를 불러오지 못했습니다." : "단어 데이터를 불러오는 중...";
    return;
  }

  const hits = state.dictionary === "kanji" ? findKanjiMatches(els.query.value) : findWordMatches(els.query.value);
  els.results.replaceChildren(...hits.map(state.dictionary === "kanji" ? renderCard : renderWordCard));
  if (!els.query.value.trim()) {
    els.status.textContent =
      state.dictionary === "kanji"
        ? `${state.records.length.toLocaleString()}자 수록. 구자체나 신자체를 입력해 보세요.`
        : `${state.words.length.toLocaleString()}개 단어 수록. 일본어 단어나 한국어 뜻을 입력해 보세요.`;
  } else if (hits.length) {
    els.status.textContent = `${hits.length.toLocaleString()}개 결과`;
  } else {
    els.status.textContent = "검색 결과가 없습니다.";
  }
}

function setDictionary(dictionary) {
  state.dictionary = dictionary;
  els.dictionaryTabs.forEach((button) => button.classList.toggle("active", button.dataset.dictionary === dictionary));
  els.filterBox.classList.toggle("hidden", dictionary !== "kanji");
  els.query.placeholder = dictionary === "kanji" ? "예: 亞, 亜, ア, あ, ひがし" : "예: 学校, がっこう, 배우다, 日本語";
  els.query.value = "";
  render();
  if (dictionary === "words" && state.wordStatus === "idle") loadWords();
}

async function loadWords() {
  state.wordStatus = "loading";
  render();
  try {
    const response = await fetch("data/words.json");
    const payload = await response.json();
    state.words = payload.records;
    state.wordStatus = "ready";
  } catch (error) {
    state.wordStatus = "error";
    console.error(error);
  }
  render();
}

async function init() {
  const kanjiResponse = await fetch("data/kanji.json");
  const payload = await kanjiResponse.json();
  state.records = payload.records;
  state.byLiteral = new Map(payload.records.map((record) => [record.literal, record]));
  state.oldToNew = new Map(Object.entries(payload.oldToNew));
  render();
}

els.query.addEventListener("input", render);
els.dictionaryTabs.forEach((button) => {
  button.addEventListener("click", () => setDictionary(button.dataset.dictionary));
});
els.filters.forEach((button) => {
  button.addEventListener("click", () => {
    state.mode = button.dataset.mode;
    els.filters.forEach((item) => item.classList.toggle("active", item === button));
    render();
  });
});

init().catch((error) => {
  els.status.textContent = "데이터를 불러오지 못했습니다. 로컬 서버로 실행해 주세요.";
  console.error(error);
});
