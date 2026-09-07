const state = {
  dictionary: "kanji",
  mode: "auto",
  records: [],
  jukujikun: [],
  byLiteral: new Map(),
  oldToNew: new Map(),
};

const els = {
  query: document.querySelector("#query"),
  status: document.querySelector("#status"),
  results: document.querySelector("#results"),
  template: document.querySelector("#card-template"),
  jukujikunTemplate: document.querySelector("#jukujikun-template"),
  filters: document.querySelectorAll("[data-mode]"),
  filterGroup: document.querySelector(".filters"),
  dictionaries: document.querySelectorAll("[data-dictionary]"),
};

function kanaFold(value) {
  return value.replace(/[\u3041-\u3096]/g, (char) =>
    String.fromCharCode(char.charCodeAt(0) + 0x60)
  );
}

function cleanReading(value) {
  return kanaFold(value.replace(/[.\-\s]/g, ""));
}

function labelList(values, empty = "자료 없음") {
  return values && values.length ? values.join(" · ") : empty;
}

function normalizeKanji(value) {
  return [...value].map((char) => state.oldToNew.get(char) || char).join("");
}

function buildSearchText(record) {
  return [
    record.literal,
    ...record.oldForms,
    ...record.variants,
    ...record.on,
    ...record.kun,
    ...record.meanings,
  ]
    .join(" ")
    .toLowerCase();
}

function findMatches(rawQuery) {
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

  node.querySelector(".on").textContent = labelList(record.on);
  node.querySelector(".kun").textContent = labelList(record.kun);
  node.querySelector(".old").textContent = labelList(record.oldForms);
  node.querySelector(".variants").textContent = labelList(record.variants);
  node.querySelector(".meanings").textContent = labelList(record.meanings);
  return node;
}

function findJukujikunMatches(rawQuery) {
  const query = rawQuery.trim();
  if (!query) return [];

  const normalizedQuery = normalizeKanji(query);
  const foldedQuery = cleanReading(query.toLowerCase());

  return state.jukujikun
    .filter((record) => {
      const text = [
        record.writing,
        record.normalizedWriting,
        ...record.readings,
        ...record.allReadings,
        ...record.meanings,
      ]
        .join(" ")
        .toLowerCase();
      const readings = cleanReading([...record.readings, ...record.allReadings].join(" ").toLowerCase());
      return (
        text.includes(query.toLowerCase()) ||
        text.includes(normalizedQuery.toLowerCase()) ||
        readings.includes(foldedQuery)
      );
    })
    .slice(0, 100);
}

function renderJukujikunCard(record) {
  const node = els.jukujikunTemplate.content.firstElementChild.cloneNode(true);
  node.querySelector(".writing").textContent = record.writing;
  node.querySelector(".reading").textContent = labelList(record.readings);
  node.querySelector(".word-meanings").textContent = labelList(record.meanings);
  node.querySelector(".word-readings").textContent = labelList(
    record.allReadings.filter((reading) => !record.readings.includes(reading))
  );
  node.querySelector(".word-info").textContent = labelList([...record.info, ...record.misc]);
  node.querySelector(".word-priority").textContent = labelList(record.priority);
  return node;
}

function render() {
  if (state.dictionary === "jukujikun") {
    const hits = findJukujikunMatches(els.query.value);
    els.results.replaceChildren(...hits.map(renderJukujikunCard));
    if (!els.query.value.trim()) {
      els.status.textContent = `${state.jukujikun.length.toLocaleString()}개 숙자훈 항목 수록. 예: 今日, 明日, 躑躅, つつじ`;
    } else if (hits.length) {
      els.status.textContent = `${hits.length.toLocaleString()}개 결과`;
    } else {
      els.status.textContent = "검색 결과가 없습니다.";
    }
    return;
  }

  const hits = findMatches(els.query.value);
  els.results.replaceChildren(...hits.map(renderCard));
  if (!els.query.value.trim()) {
    els.status.textContent = `${state.records.length.toLocaleString()}자 수록. 구자체나 신자체를 입력해 보세요.`;
  } else if (hits.length) {
    els.status.textContent = `${hits.length.toLocaleString()}개 결과`;
  } else {
    els.status.textContent = "검색 결과가 없습니다.";
  }
}

function setDictionary(dictionary) {
  state.dictionary = dictionary;
  els.dictionaries.forEach((item) => item.classList.toggle("active", item.dataset.dictionary === dictionary));
  els.filterGroup.classList.toggle("hidden", dictionary !== "kanji");
  els.query.placeholder =
    dictionary === "kanji" ? "예: 亞, 亜, ア, あ, ひがし" : "예: 今日, 明日, 躑躅, つつじ";
  els.query.value = "";
  render();
}

async function init() {
  const [kanjiResponse, jukujikunResponse] = await Promise.all([
    fetch("data/kanji.json"),
    fetch("data/jukujikun.json"),
  ]);
  const payload = await kanjiResponse.json();
  const jukujikunPayload = await jukujikunResponse.json();
  state.records = payload.records;
  state.jukujikun = jukujikunPayload.records;
  state.byLiteral = new Map(payload.records.map((record) => [record.literal, record]));
  state.oldToNew = new Map(Object.entries(payload.oldToNew));
  render();
}

els.query.addEventListener("input", render);
els.filters.forEach((button) => {
  button.addEventListener("click", () => {
    state.mode = button.dataset.mode;
    els.filters.forEach((item) => item.classList.toggle("active", item === button));
    render();
  });
});
els.dictionaries.forEach((button) => {
  button.addEventListener("click", () => setDictionary(button.dataset.dictionary));
});

init().catch((error) => {
  els.status.textContent = "데이터를 불러오지 못했습니다. 로컬 서버로 실행해 주세요.";
  console.error(error);
});
