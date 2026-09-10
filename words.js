const WORD_TERM = 0;
const WORD_READING = 1;
const WORD_MEANINGS = 2;
const WORD_PARTS = 3;
const WORD_LEVELS = 4;
const WORD_CLASSES = 5;
const WORD_FREQUENCY_RANK = 6;
const WORD_SOURCE_COUNT = 7;
const LEVEL_RANKS = new Map([
  ["초급", 0],
  ["중급", 1],
  ["고급", 2],
]);
const KOREAN_QUERY_WORD_RANKS = new Map([
  ["되다", new Map([["なる", 0], ["出来る", 1], ["できる", 1], ["成る", 2]])],
  ["하다", new Map([["する", 0], ["為る", 1]])],
  ["있다", new Map([["ある", 0], ["有る", 1], ["いる", 2], ["居る", 3]])],
  ["없다", new Map([["ない", 0], ["無い", 1]])],
  ["가다", new Map([["行く", 0], ["いく", 0], ["ゆく", 1], ["逝く", 2]])],
  ["오다", new Map([["来る", 0], ["くる", 0]])],
  ["보다", new Map([["見る", 0], ["みる", 0]])],
  ["말하다", new Map([["言う", 0], ["いう", 0], ["話す", 1], ["はなす", 1]])],
  ["알다", new Map([["分かる", 0], ["わかる", 0], ["知る", 1], ["しる", 1]])],
]);

const state = {
  count: null,
  buckets: new Map(),
  bucketStatus: new Map(),
};

const els = {
  query: document.querySelector("#query"),
  status: document.querySelector("#status"),
  results: document.querySelector("#results"),
  template: document.querySelector("#word-card-template"),
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

function bucketKey(value) {
  return Array.from(cleanWord(value))[0] || "";
}

function bucketFilename(key) {
  return key ? `u${key.codePointAt(0).toString(16)}.json` : "";
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

function wordClasses(record) {
  return record[WORD_CLASSES] || [];
}

function wordFrequencyRank(record) {
  return record[WORD_FREQUENCY_RANK] ?? 9000;
}

function wordSourceCount(record) {
  return record[WORD_SOURCE_COUNT] || 0;
}

function wordLevelRank(record) {
  return Math.min(...wordLevels(record).map((level) => LEVEL_RANKS.get(level) ?? 9), 8);
}

function wordSortValue(record) {
  return cleanWord(wordReading(record) || wordTerm(record));
}

function isKoreanQuery(value) {
  return /[가-힣]/.test(value);
}

function labelList(values, empty = "자료 없음") {
  return values && values.length ? values.join(" · ") : empty;
}

function buildSearchText(record) {
  return [wordTerm(record), wordReading(record), ...wordMeanings(record), ...wordParts(record), ...wordClasses(record), ...wordLevels(record)]
    .join(" ")
    .toLowerCase();
}

function wordScore(record, query, foldedQuery) {
  const term = wordTerm(record).toLowerCase();
  const reading = wordReading(record).toLowerCase();
  const foldedTerm = cleanWord(wordTerm(record));
  const foldedReading = cleanWord(wordReading(record));
  const meaningList = wordMeanings(record).map((meaning) => meaning.toLowerCase());
  const meanings = wordMeanings(record).join(" ").toLowerCase();
  const searchText = buildSearchText(record);

  if (term === query || reading === query) return 0;
  if (foldedTerm === foldedQuery || foldedReading === foldedQuery) return 1;
  if (term.startsWith(query) || reading.startsWith(query)) return 2;
  if (foldedTerm.startsWith(foldedQuery) || foldedReading.startsWith(foldedQuery)) return 3;
  if (term.includes(query) || reading.includes(query)) return 4;
  if (foldedTerm.includes(foldedQuery) || foldedReading.includes(foldedQuery)) return 5;
  if (meaningList.includes(query)) return 6;
  if (meaningList.some((meaning) => meaning.startsWith(query))) return 7;
  if (meanings.includes(query)) return 8;
  if (searchText.includes(query)) return 9;
  return null;
}

function meaningMatchRank(record, query) {
  const meanings = wordMeanings(record).map((meaning) => meaning.toLowerCase());
  const exactIndex = meanings.findIndex((meaning) => meaning === query);
  if (exactIndex >= 0) return exactIndex;
  const prefixIndex = meanings.findIndex((meaning) => meaning.startsWith(query));
  return prefixIndex >= 0 ? prefixIndex + 20 : 99;
}

function meaningBreadth(record, score) {
  return score >= 6 ? wordMeanings(record).length : 0;
}

function preferredMeaningRank(record, query) {
  if (!isKoreanQuery(query)) return 99;
  const ranks = KOREAN_QUERY_WORD_RANKS.get(query);
  if (!ranks) return 99;
  const term = wordTerm(record);
  return Math.min(ranks.get(term) ?? 99, ranks.get(cleanWord(term)) ?? 99);
}

function displayMeanings(record, rawQuery) {
  const query = rawQuery.trim().toLowerCase();
  const meanings = wordMeanings(record);
  if (!isKoreanQuery(query)) return meanings;

  return meanings
    .map((meaning, index) => {
      const value = meaning.toLowerCase();
      let rank = 3;
      if (value === query) rank = 0;
      else if (value.startsWith(query)) rank = 1;
      else if (value.includes(query)) rank = 2;
      return { meaning, index, rank };
    })
    .sort((a, b) => a.rank - b.rank || a.index - b.index)
    .map((item) => item.meaning);
}

function findMatches(rawQuery, records) {
  const query = rawQuery.trim().toLowerCase();
  if (!query) return [];

  const foldedQuery = cleanWord(query);
  return records
    .map((record) => ({ record, score: wordScore(record, query, foldedQuery) }))
    .filter((hit) => hit.score !== null)
    .sort((a, b) =>
      a.score - b.score ||
      preferredMeaningRank(a.record, query) - preferredMeaningRank(b.record, query) ||
      meaningMatchRank(a.record, query) - meaningMatchRank(b.record, query) ||
      meaningBreadth(a.record, a.score) - meaningBreadth(b.record, b.score) ||
      wordFrequencyRank(a.record) - wordFrequencyRank(b.record) ||
      wordSourceCount(b.record) - wordSourceCount(a.record) ||
      wordLevelRank(a.record) - wordLevelRank(b.record) ||
      wordSortValue(a.record).localeCompare(wordSortValue(b.record), "ja") ||
      wordTerm(a.record).length - wordTerm(b.record).length ||
      wordTerm(a.record).localeCompare(wordTerm(b.record), "ja")
    )
    .slice(0, 100);
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

function renderCard(hit, query) {
  const node = els.template.content.firstElementChild.cloneNode(true);
  const { record } = hit;
  const term = wordTerm(record);
  const reading = wordReading(record);
  const termNode = node.querySelector(".word-term");
  termNode.replaceChildren(createRubyForTerm(term, reading));

  const readingNode = node.querySelector(".word-reading");
  if (reading && reading !== term && (!hasKanji(term) || /[・･]/.test(reading))) {
    readingNode.textContent = reading;
  } else {
    readingNode.classList.add("hidden");
  }

  node.querySelector(".word-meanings").textContent = labelList(displayMeanings(record, query));
  node.querySelector(".word-pos").textContent = labelList([...wordParts(record), ...wordClasses(record)]);
  node.querySelector(".word-levels").textContent = labelList(wordLevels(record));
  return node;
}

function render() {
  const query = els.query.value.trim();
  if (!query) {
    els.results.replaceChildren();
    const count = state.count ? `${state.count.toLocaleString()}개 단어 수록. ` : "";
    els.status.textContent = `${count}일본어 단어나 한국어 뜻을 입력해 보세요.`;
    return;
  }

  const key = bucketKey(query);
  const filename = bucketFilename(key);
  if (!filename) {
    els.results.replaceChildren();
    els.status.textContent = "검색 결과가 없습니다.";
    return;
  }

  if (state.bucketStatus.get(filename) === "error") {
    els.results.replaceChildren();
    els.status.textContent = "검색 데이터를 불러오지 못했습니다.";
    return;
  }

  if (!state.buckets.has(filename)) {
    loadBucket(filename);
    els.results.replaceChildren();
    els.status.textContent = "검색 데이터를 불러오는 중...";
    return;
  }

  const hits = findMatches(query, state.buckets.get(filename));
  els.results.replaceChildren(...hits.map((hit) => renderCard(hit, query)));
  if (hits.length) {
    els.status.textContent = `${hits.length.toLocaleString()}개 결과`;
  } else {
    els.status.textContent = "검색 결과가 없습니다.";
  }
}

async function loadBucket(filename) {
  if (state.bucketStatus.get(filename) === "loading") return;
  state.bucketStatus.set(filename, "loading");
  try {
    const response = await fetch(`data/words/${filename}`);
    if (!response.ok) {
      state.buckets.set(filename, []);
      state.bucketStatus.set(filename, "ready");
      render();
      return;
    }
    const records = await response.json();
    state.buckets.set(filename, records);
    state.bucketStatus.set(filename, "ready");
  } catch (error) {
    state.bucketStatus.set(filename, "error");
    console.error(error);
  }
  render();
}

async function init() {
  try {
    const response = await fetch("data/words/meta.json");
    const payload = await response.json();
    state.count = payload.count;
  } catch (error) {
    console.warn(error);
  }
  render();
}

els.query.addEventListener("input", render);

init().catch((error) => {
  els.status.textContent = "데이터를 불러오지 못했습니다. 로컬 서버로 실행해 주세요.";
  console.error(error);
});
