const state = {
  mode: "auto",
  records: [],
  byLiteral: new Map(),
  oldToNew: new Map(),
};

const els = {
  query: document.querySelector("#query"),
  status: document.querySelector("#status"),
  results: document.querySelector("#results"),
  template: document.querySelector("#card-template"),
  filters: document.querySelectorAll("[data-mode]"),
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

function render() {
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

async function init() {
  const response = await fetch("data/kanji.json");
  const payload = await response.json();
  state.records = payload.records;
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

init().catch((error) => {
  els.status.textContent = "데이터를 불러오지 못했습니다. 로컬 서버로 실행해 주세요.";
  console.error(error);
});
