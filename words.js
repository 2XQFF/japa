const WORD_TERM = 0;
const WORD_READING = 1;
const WORD_MEANINGS = 2;
const WORD_PARTS = 3;
const WORD_LEVELS = 4;
const WORD_CLASSES = 5;
const WORD_FREQUENCY_RANK = 6;
const WORD_SOURCE_COUNT = 7;
const WORD_DATA_VERSION = "20260910-kanji-compounds-2";
const LEVEL_RANKS = new Map([
  ["초급", 0],
  ["중급", 1],
  ["고급", 2],
]);
const KOREAN_QUERY_WORD_RANKS = new Map([
  ["되다", new Map([["なる", 0], ["出来る", 1], ["できる", 1], ["成る", 2]])],
  ["하다", new Map([["する", 0], ["為る:する", 1]])],
  ["있다", new Map([["ある", 0], ["有る", 1], ["いる", 2], ["居る", 3]])],
  ["없다", new Map([["ない", 0], ["無い", 1]])],
  ["좋다", new Map([["いい", 0], ["良い", 1]])],
  ["좋아하다", new Map([["好きだ", 0], ["好む", 1], ["好く", 2]])],
  ["싫다", new Map([["嫌いだ", 0]])],
  ["나쁘다", new Map([["悪い", 0]])],
  ["크다", new Map([["大きい", 0]])],
  ["작다", new Map([["小さい", 0]])],
  ["많다", new Map([["多い", 0]])],
  ["적다", new Map([["少ない", 0]])],
  ["높다", new Map([["高い", 0]])],
  ["비싸다", new Map([["高い", 0]])],
  ["싸다", new Map([["安い", 0]])],
  ["새롭다", new Map([["新しい", 0]])],
  ["낡다", new Map([["古い", 0]])],
  ["빠르다", new Map([["早い", 0]])],
  ["늦다", new Map([["遅い", 0]])],
  ["덥다", new Map([["暑い", 0]])],
  ["뜨겁다", new Map([["熱い", 0]])],
  ["춥다", new Map([["寒い", 0]])],
  ["차갑다", new Map([["冷たい", 0]])],
  ["좁다", new Map([["狭い", 0]])],
  ["넓다", new Map([["広い", 0]])],
  ["쉽다", new Map([["易しい", 0]])],
  ["어렵다", new Map([["難しい", 0]])],
  ["재미있다", new Map([["面白い", 0]])],
  ["파랗다", new Map([["青い", 0]])],
  ["푸르다", new Map([["青い", 0]])],
  ["붉다", new Map([["赤い", 0]])],
  ["빨갛다", new Map([["赤い", 0]])],
  ["하얗다", new Map([["白い", 0]])],
  ["검다", new Map([["黒い", 0]])],
  ["가다", new Map([["行く:いく", 0], ["行く:ゆく", 1], ["行く", 1], ["いく", 2], ["ゆく", 3], ["逝く", 4]])],
  ["오다", new Map([["来る", 0], ["くる", 0]])],
  ["보다", new Map([["見る", 0], ["みる", 0]])],
  ["듣다", new Map([["聞く", 0]])],
  ["읽다", new Map([["読む", 0]])],
  ["쓰다", new Map([["使う", 0], ["書く", 1]])],
  ["먹다", new Map([["食べる", 0], ["食う", 1], ["喰う", 2]])],
  ["마시다", new Map([["飲む", 0]])],
  ["자다", new Map([["寝る", 0]])],
  ["일어나다", new Map([["起きる", 0]])],
  ["사다", new Map([["買う", 0]])],
  ["팔다", new Map([["売る", 0]])],
  ["기다리다", new Map([["待つ", 0]])],
  ["만들다", new Map([["作る", 0]])],
  ["잡다", new Map([["取る", 0]])],
  ["가지다", new Map([["持つ", 0]])],
  ["생각하다", new Map([["思う", 0]])],
  ["말하다", new Map([["言う", 0], ["いう", 0], ["話す", 1], ["はなす", 1]])],
  ["알다", new Map([["分かる", 0], ["わかる", 0], ["知る", 1], ["しる", 1]])],
  ["울다", new Map([["鳴る", 0]])],
  ["만나다", new Map([["会う", 0]])],
  ["돌아가다", new Map([["帰る", 0]])],
  ["걷다", new Map([["歩く", 0]])],
  ["달리다", new Map([["走る", 0]])],
  ["헤엄치다", new Map([["泳ぐ", 0]])],
  ["쉬다", new Map([["休む", 0]])],
  ["일하다", new Map([["働く", 0]])],
  ["공부하다", new Map([["勉強する", 0], ["学習する", 1], ["勉学する", 2]])],
  ["가르치다", new Map([["教える", 0]])],
  ["배우다", new Map([["習う", 0]])],
  ["잊다", new Map([["忘れる", 0]])],
  ["기억하다", new Map([["覚える", 0]])],
  ["죽다", new Map([["死ぬ", 0]])],
  ["태어나다", new Map([["生まれる", 0]])],
  ["살다", new Map([["住む", 0]])],
  ["타다", new Map([["乗る", 0]])],
  ["내리다", new Map([["下ろす", 0], ["下げる", 1], ["降りる", 2]])],
  ["입다", new Map([["着る", 0], ["穿く", 1], ["被る", 2]])],
  ["신다", new Map([["履く", 0]])],
  ["벗다", new Map([["脱ぐ", 0]])],
  ["씻다", new Map([["洗う", 0]])],
  ["닦다", new Map([["磨く", 0]])],
  ["자르다", new Map([["切る", 0]])],
  ["빌려주다", new Map([["貸す", 0]])],
  ["빌리다", new Map([["借りる", 0]])],
  ["돌려주다", new Map([["返す", 0]])],
  ["보내다", new Map([["送る", 0]])],
  ["열다", new Map([["開ける", 0]])],
  ["열리다", new Map([["開く", 0]])],
  ["닫다", new Map([["閉める", 0]])],
  ["닫히다", new Map([["閉まる", 0]])],
  ["서다", new Map([["立つ", 0]])],
  ["앉다", new Map([["座る", 0]])],
  ["올리다", new Map([["上げる", 0]])],
  ["오르다", new Map([["上がる", 0], ["上る", 1]])],
  ["내려가다", new Map([["下がる", 0], ["下る", 1]])],
  ["들어가다", new Map([["入る", 0]])],
  ["넣다", new Map([["入れる", 0]])],
  ["나오다", new Map([["出る", 0]])],
  ["내다", new Map([["出す", 0]])],
  ["어둡다", new Map([["暗い", 0]])],
  ["밝다", new Map([["明るい", 0]])],
  ["가깝다", new Map([["近い", 0]])],
  ["멀다", new Map([["遠い", 0]])],
  ["강하다", new Map([["強い", 0]])],
  ["약하다", new Map([["弱い", 0]])],
  ["굵다", new Map([["太い", 0]])],
  ["가늘다", new Map([["細い", 0]])],
  ["무겁다", new Map([["重い", 0]])],
  ["가볍다", new Map([["軽い", 0]])],
  ["달다", new Map([["甘い", 0]])],
  ["맵다", new Map([["辛い:からい", 0], ["辛い", 0]])],
  ["괴롭다", new Map([["辛い:つらい", 0], ["辛い", 0]])],
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

function wordDataUrl(filename) {
  return `data/words/${filename}?v=${WORD_DATA_VERSION}`;
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
  if (!wordMeanings(record).some((meaning) => meaning.toLowerCase() === query)) return 99;
  const ranks = KOREAN_QUERY_WORD_RANKS.get(query);
  if (!ranks) return 99;
  const term = wordTerm(record);
  const reading = primaryReading(wordReading(record));
  return Math.min(
    ranks.get(`${term}:${reading}`) ?? 99,
    ranks.get(term) ?? 99,
    ranks.get(cleanWord(term)) ?? 99
  );
}

function compareWordOrder(a, b) {
  return (
    wordFrequencyRank(a.record) - wordFrequencyRank(b.record) ||
    wordSourceCount(b.record) - wordSourceCount(a.record) ||
    wordLevelRank(a.record) - wordLevelRank(b.record) ||
    wordSortValue(a.record).localeCompare(wordSortValue(b.record), "ja") ||
    wordTerm(a.record).length - wordTerm(b.record).length ||
    wordTerm(a.record).localeCompare(wordTerm(b.record), "ja")
  );
}

function compareHits(a, b, query) {
  if (isKoreanQuery(query)) {
    return (
      meaningMatchRank(a.record, query) - meaningMatchRank(b.record, query) ||
      preferredMeaningRank(a.record, query) - preferredMeaningRank(b.record, query) ||
      compareWordOrder(a, b) ||
      a.score - b.score
    );
  }

  return (
    a.score - b.score ||
    preferredMeaningRank(a.record, query) - preferredMeaningRank(b.record, query) ||
    meaningMatchRank(a.record, query) - meaningMatchRank(b.record, query) ||
    meaningBreadth(a.record, a.score) - meaningBreadth(b.record, b.score) ||
    compareWordOrder(a, b)
  );
}

function dedupeHits(hits) {
  const seen = new Set();
  return hits.filter((hit) => {
    const key = `${wordTerm(hit.record)}\t${wordMeanings(hit.record).join("\t")}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
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
  const hits = records
    .map((record) => ({ record, score: wordScore(record, query, foldedQuery) }))
    .filter((hit) => hit.score !== null)
    .sort((a, b) => compareHits(a, b, query));
  return dedupeHits(hits).slice(0, 100);
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
    const response = await fetch(wordDataUrl(filename), { cache: "no-cache" });
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
    const response = await fetch(wordDataUrl("meta.json"), { cache: "no-cache" });
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
