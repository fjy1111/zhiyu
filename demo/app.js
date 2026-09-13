const app = document.querySelector("#app");
const navButtons = Array.from(document.querySelectorAll("nav button"));

const PAGE_TITLES = {
  overview: "安全总览",
  admission: "知识库安全准入",
  kb: "安全知识库 / 隔离中心",
  rag: "RAG 安全对照",
  eval: "实验评估",
};

const MECHANISM_LABELS = {
  NORMAL: "正常文档",
  FACT_TAMPERING: "事实篡改",
  PROMPT_INJECTION: "提示注入",
  HIDDEN_INSTRUCTION: "隐藏指令",
  RETRIEVAL_HIJACKING: "检索劫持",
  KNOWLEDGE_CONFLICT: "知识冲突",
};

const DECISION_META = {
  SAFE: { tone: "safe", title: "SAFE", desc: "允许自动准入 Protected KB" },
  REVIEW: { tone: "review", title: "REVIEW", desc: "隔离等待复核 · 未自动进入 Protected KB" },
  POISON: { tone: "poison", title: "POISON", desc: "自动阻断 · 禁止进入 Protected KB" },
  CURATED_TRUSTED_SEED: { tone: "safe", title: "TRUSTED", desc: "预先审核可信基线" },
};

const state = {
  currentPage: "overview",
  scenarios: [],
  presets: [],
  backendState: null,
  selectedMechanism: "FACT_TAMPERING",
  selectedScenarioId: null,
  scanResult: null,
  ragResult: null,
  ragQuery: "",
  kbTab: "trusted",
  loading: false,
  error: "",
  toast: "",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function apiGet(path) {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `GET ${path} failed (${response.status})`);
  return data;
}

async function apiPost(path, payload = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `POST ${path} failed (${response.status})`);
  return data;
}

function mechanismLabel(value) {
  return MECHANISM_LABELS[value] || value || "未知机制";
}

function decisionMeta(value) {
  return DECISION_META[value] || { tone: "neutral", title: value || "UNKNOWN", desc: "暂无说明" };
}

function statusBadge(value, compact = false) {
  const meta = decisionMeta(value);
  return `<span class="status-badge ${meta.tone} ${compact ? "compact" : ""}">${escapeHtml(meta.title)}</span>`;
}

function formatScore(value) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(4) : "—";
}

function shorten(text, max = 180) {
  const value = String(text ?? "").trim();
  if (!value) return "暂无文本";
  return value.length > max ? `${value.slice(0, max)}…` : value;
}

function currentScenario() {
  return state.scenarios.find((x) => x.scenario_id === state.selectedScenarioId) || null;
}

function filteredScenarios() {
  return state.scenarios.filter((x) => x.mechanism === state.selectedMechanism);
}

function scenarioName(scenario) {
  if (!scenario) return "未选择场景";
  const topic = scenario.topic_display_name || "";
  if (topic && !topic.endsWith("？")) return topic;
  return scenario.display_name || scenario.scenario_id;
}

function setToast(message) {
  state.toast = message;
  renderToast();
  window.clearTimeout(setToast.timer);
  setToast.timer = window.setTimeout(() => {
    state.toast = "";
    renderToast();
  }, 2200);
}

function renderToast() {
  let node = document.querySelector("#global-toast");
  if (!node) {
    node = document.createElement("div");
    node.id = "global-toast";
    node.className = "toast";
    document.body.appendChild(node);
  }
  node.textContent = state.toast;
  node.classList.toggle("show", Boolean(state.toast));
}

function updateNavActive() {
  navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.page === state.currentPage);
  });
}

function navigate(page) {
  state.currentPage = page;
  state.error = "";
  updateNavActive();
  renderApp();
}

async function refreshBackendState() {
  state.backendState = await apiGet("/api/state");
}

async function loadInitialData() {
  state.loading = true;
  renderApp();
  try {
    const [scenarios, presets, backendState] = await Promise.all([
      apiGet("/api/scenarios"),
      apiGet("/api/presets"),
      apiGet("/api/state"),
    ]);
    state.scenarios = Array.isArray(scenarios) ? scenarios : [];
    state.presets = Array.isArray(presets) ? presets : [];
    state.backendState = backendState || {};
    const first = state.scenarios.find((x) => x.mechanism === state.selectedMechanism) || state.scenarios[0];
    if (first) {
      state.selectedMechanism = first.mechanism;
      state.selectedScenarioId = first.scenario_id;
      state.ragQuery = first.primary_question || "";
    }
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    renderApp();
  }
}

function pageHeader(title, subtitle, rightHtml = "") {
  return `
    <section class="page-header">
      <div>
        <div class="eyebrow">ZhiYu · Competition Demo</div>
        <h2>${escapeHtml(title)}</h2>
        <p>${escapeHtml(subtitle)}</p>
      </div>
      <div class="page-header-actions">${rightHtml}</div>
    </section>
  `;
}

function renderError() {
  if (!state.error) return "";
  return `
    <div class="error-card">
      <strong>操作失败</strong>
      <span>${escapeHtml(state.error)}</span>
    </div>
  `;
}

function renderOverview() {
  const counts = state.backendState?.counts || {};
  const statCards = [
    ["预先审核可信基线", counts.trusted ?? 0, "Curated Trusted Seed", "blue", "✓"],
    ["Protected KB", counts.protected ?? 0, "当前可供安全检索", "cyan", "◆"],
    ["REVIEW 隔离", counts.review ?? 0, "等待人工复核", "orange", "!"],
    ["POISON 阻断", counts.poison ?? 0, "禁止进入安全知识库", "red", "×"],
  ];

  const pipeline = [
    "文档接入",
    "规则扫描",
    "语义分析",
    "证据构建",
    "统一风险判断",
    "SAFE / REVIEW / POISON",
    "Protected KB",
  ];

  return `
    ${pageHeader(
      "安全总览",
      "面向 RAG 知识库的投毒检测与主动防御系统",
      '<div class="online-pill"><span></span>Security Gateway 运行正常</div>'
    )}
    ${renderError()}

    <section class="stats-grid">
      ${statCards.map(([label, value, note, tone, icon]) => `
        <article class="stat-card ${tone}">
          <div class="stat-icon">${icon}</div>
          <div class="stat-copy">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
            <small>${escapeHtml(note)}</small>
          </div>
        </article>
      `).join("")}
    </section>

    <section class="panel pipeline-panel">
      <div class="section-heading">
        <div>
          <span class="section-kicker">SECURITY PIPELINE</span>
          <h3>ZhiYu 安全链路</h3>
        </div>
        <span class="muted">Evidence First, Judgment Second</span>
      </div>
      <div class="pipeline">
        ${pipeline.map((name, index) => `
          <div class="pipeline-node ${index === pipeline.length - 1 ? "final" : ""}">
            <span class="pipeline-index">${String(index + 1).padStart(2, "0")}</span>
            <strong>${escapeHtml(name)}</strong>
          </div>
          ${index < pipeline.length - 1 ? '<div class="pipeline-arrow">→</div>' : ""}
        `).join("")}
      </div>
    </section>

    <section class="overview-bottom-grid">
      <article class="principle-card">
        <span class="section-kicker">CORE PRINCIPLE</span>
        <h3>Evidence First, Judgment Second</h3>
        <p>先构建安全证据，再进行风险判断。LLM 负责解释证据，程序负责最终风险决策。</p>
        <div class="principle-rules">
          <span>UNKNOWN ≠ POISON</span>
          <span>INSUFFICIENT_EVIDENCE ≠ POISON</span>
          <span>CONTRADICTORY ≠ 自动 POISON</span>
        </div>
      </article>

      <article class="cta-card">
        <div>
          <span class="section-kicker">LIVE DEMO</span>
          <h3>开始安全准入演示</h3>
          <p>从事实篡改、提示注入、检索劫持等真实演示场景出发，观察攻击文档如何被隔离。</p>
        </div>
        <button class="primary large" data-action="go-admission">进入安全准入</button>
      </article>
    </section>
  `;
}

function renderMechanismTabs() {
  return Object.entries(MECHANISM_LABELS).map(([key, label]) => `
    <button class="mechanism-tab ${state.selectedMechanism === key ? "active" : ""}" data-mechanism="${key}">
      ${escapeHtml(label)}
    </button>
  `).join("");
}

function renderScenarioSelect(id = "scenario-select") {
  return `
    <select id="${id}" class="scenario-select">
      ${filteredScenarios().map((scenario) => `
        <option value="${escapeHtml(scenario.scenario_id)}" ${scenario.scenario_id === state.selectedScenarioId ? "selected" : ""}>
          ${escapeHtml(scenarioName(scenario))} · ${escapeHtml(scenario.scenario_id)}
        </option>
      `).join("")}
    </select>
  `;
}

function renderFieldComparison(scenario) {
  if (!scenario || !["FACT_TAMPERING", "KNOWLEDGE_CONFLICT"].includes(scenario.mechanism)) return "";
  return `
    <section class="field-comparison">
      <div class="comparison-label">${escapeHtml(scenario.queried_field || "关键字段")}</div>
      <div class="value-card trusted">
        <small>预先审核可信基线</small>
        <strong>${escapeHtml(scenario.trusted_value ?? "可信值暂未提供")}</strong>
      </div>
      <div class="vs-badge">VS</div>
      <div class="value-card incoming">
        <small>Incoming</small>
        <strong>${escapeHtml(scenario.incoming_value ?? "Incoming 值暂未提供")}</strong>
      </div>
    </section>
  `;
}

function renderComponentStatuses(result) {
  const obj = result?.component_statuses;
  if (!obj || typeof obj !== "object" || !Object.keys(obj).length) return "";
  const labels = { OK: "正常", ERROR: "组件异常", INVALID_OUTPUT: "输出异常" };
  return `
    <div class="subsection">
      <h4>组件状态</h4>
      <div class="evidence-grid">
        ${Object.entries(obj).map(([key, count]) => `
          <div class="evidence-card">
            <span class="evidence-key">${escapeHtml(key)}</span>
            <strong>${escapeHtml(labels[key] || key)}</strong>
            <small>${escapeHtml(count)} 项</small>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

function renderFactualEvidence(result) {
  const obj = result?.factual_evidence_summary;
  if (!obj || typeof obj !== "object" || !Object.keys(obj).length) return "";
  const labels = {
    SUPPORTED: "支持证据",
    CONTRADICTORY: "冲突证据",
    INSUFFICIENT_EVIDENCE: "证据不足",
  };
  return `
    <div class="subsection">
      <h4>事实证据</h4>
      <div class="evidence-grid">
        ${Object.entries(obj).map(([key, count]) => `
          <div class="evidence-card">
            <span class="evidence-key">${escapeHtml(key)}</span>
            <strong>${escapeHtml(labels[key] || key)}</strong>
            <small>${escapeHtml(count)} 项</small>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

function renderDecision(result) {
  if (!result) {
    return `
      <div class="gateway-empty">
        <div class="gateway-orb">◎</div>
        <h3>等待检测</h3>
        <p>选择 Incoming Document 后执行安全扫描，结果将在这里展示。</p>
      </div>
    `;
  }
  const meta = decisionMeta(result.actual_decision);
  return `
    <div class="decision-card ${meta.tone}">
      <div class="decision-topline">
        <span>真实预扫描结果复现</span>
        <span>${escapeHtml(result.prescan_mode || "真实预扫描结果复现")}</span>
      </div>
      <div class="decision-main">
        ${statusBadge(result.actual_decision)}
        <div>
          <h3>${escapeHtml(meta.title)}</h3>
          <p>${escapeHtml(meta.desc)}</p>
        </div>
      </div>
      <div class="judge-line">
        <span>统一风险判断状态</span>
        <strong>${escapeHtml(result.judge_status || "—")}</strong>
      </div>
      ${result.judge_status === "INVALID_OUTPUT"
        ? `
          <div class="fail-closed-note">
            <strong>Fail-closed 安全策略</strong>
            <span>${
              result.actual_decision === "REVIEW"
                ? "Judge 输出异常时不自动放行，系统保守进入 REVIEW 并隔离待复核。"
                : result.actual_decision === "POISON"
                  ? "Judge 输出异常不会触发自动放行；最终决策仍由程序侧已构建安全证据与风险决策引擎给出，本场景判定为 POISON。"
                  : "Judge 输出异常不会触发自动放行；最终决策由程序侧安全证据与风险决策引擎给出。"
            }</span>
          </div>
        `
        : ""}
    </div>
    ${renderComponentStatuses(result)}
    ${renderFactualEvidence(result)}
  `;
}

function renderAdmission() {
  const scenario = currentScenario();
  return `
    ${pageHeader(
      "知识库安全准入",
      "Incoming Document 在进入知识库之前，先经过 ZhiYu Security Gateway。",
      '<button class="ghost" data-action="reset-demo">↻ 重置演示</button>'
    )}
    ${renderError()}

    <section class="panel admission-controls">
      <div class="section-heading">
        <div>
          <span class="section-kicker">ATTACK MECHANISM</span>
          <h3>选择安全场景</h3>
        </div>
        <span class="muted">最终 18 个比赛演示场景</span>
      </div>
      <div class="mechanism-tabs">${renderMechanismTabs()}</div>
      <label class="field-label" for="scenario-select">演示场景</label>
      ${renderScenarioSelect()}
    </section>

    <section class="admission-layout">
      <article class="panel scenario-panel">
        <div class="scenario-title-row">
          <div>
            <span class="section-kicker">SCENARIO</span>
            <h3>${escapeHtml(scenarioName(scenario))}</h3>
          </div>
          <div class="tag-row">
            <span class="pill">${escapeHtml(mechanismLabel(scenario?.mechanism))}</span>
            <span class="pill soft">${escapeHtml(scenario?.source_kind || "UNKNOWN_SOURCE")}</span>
          </div>
        </div>

        <dl class="scenario-meta">
          <div><dt>Scenario ID</dt><dd>${escapeHtml(scenario?.scenario_id || "—")}</dd></div>
          <div><dt>Incoming Document</dt><dd>${escapeHtml(scenario?.incoming_document_id || "无")}</dd></div>
          <div><dt>默认问题</dt><dd>${escapeHtml(scenario?.primary_question || "—")}</dd></div>
          <div>
            <dt>检测状态</dt>
            <dd>
              ${state.scanResult
                ? statusBadge(state.scanResult.actual_decision, true)
                : '<span class="pending-badge">待检测</span>'}
            </dd>
          </div>
        </dl>

        ${renderFieldComparison(scenario)}

        <div class="incoming-preview">
          <span class="section-kicker">INCOMING DOCUMENT</span>
          <strong>${escapeHtml(scenario?.incoming_document_id || "NORMAL 场景无 Incoming Attack")}</strong>
          <p>${escapeHtml(scenario?.primary_question || "请选择场景")}</p>
        </div>

        <button
          class="primary scan-button"
          data-action="scan"
          ${!scenario?.incoming_document_id || state.loading ? "disabled" : ""}
        >
          ${state.loading ? "正在执行安全分析…" : scenario?.incoming_document_id ? "执行安全检测" : "NORMAL 场景无需攻击扫描"}
        </button>
      </article>

      <article class="panel gateway-panel">
        <div class="section-heading">
          <div>
            <span class="section-kicker">SECURITY GATEWAY</span>
            <h3>ZhiYu Security Gateway</h3>
          </div>
          <span class="online-pill compact"><span></span>Ready</span>
        </div>

        <div class="gateway-steps">
          ${["规则扫描", "语义分析", "证据构建", "统一风险判断"].map((name, index) => `
            <div class="gateway-step ${state.scanResult ? "done" : state.loading && index < 3 ? "active" : ""}">
              <span>${index + 1}</span>
              <strong>${escapeHtml(name)}</strong>
              <small>${state.scanResult ? "已完成" : state.loading ? "正在分析" : "等待检测"}</small>
            </div>
          `).join("")}
        </div>

        ${renderDecision(state.scanResult)}
      </article>
    </section>
  `;
}

function docsForKbTab() {
  const backend = state.backendState || {};
  if (state.kbTab === "trusted") return backend.trusted_documents || [];
  if (state.kbTab === "protected") return backend.protected_documents || [];
  if (state.kbTab === "review") return backend.review_documents || [];
  if (state.kbTab === "poison") return backend.poison_documents || [];
  return [];
}

function renderDocumentCard(doc, tone) {
  const id = doc.demo_document_id || doc.document_id || "unknown";
  const type = doc.mechanism || doc.source_category || doc.source_kind || "DOCUMENT";
  const text = doc.runtime_text || doc.text || "";
  return `
    <article class="document-card ${tone}">
      <div class="document-card-head">
        <div>
          <span class="section-kicker">${escapeHtml(type)}</span>
          <h4>${escapeHtml(id)}</h4>
        </div>
        <span class="status-dot ${tone}"></span>
      </div>
      <p>${escapeHtml(shorten(text, 190))}</p>
      <small>${
        tone === "blue"
          ? "预先审核可信基线"
          : tone === "cyan"
            ? "当前可供安全检索"
            : tone === "orange"
              ? "隔离待复核"
              : tone === "red"
                ? "已阻断"
                : "运行时文档"
      }</small>
    </article>
  `;
}

function renderKnowledgeBase() {
  const counts = state.backendState?.counts || {};
  const tabs = [
    ["trusted", "预先审核可信基线", counts.trusted ?? 0, "blue"],
    ["protected", "Protected KB", counts.protected ?? 0, "cyan"],
    ["review", "REVIEW 隔离区", counts.review ?? 0, "orange"],
    ["poison", "POISON 阻断区", counts.poison ?? 0, "red"],
  ];
  const docs = docsForKbTab();
  const tone = tabs.find((x) => x[0] === state.kbTab)?.[3] || "blue";

  return `
    ${pageHeader(
      "安全知识库 / 隔离中心",
      "查看文档在安全准入后进入 Protected KB、REVIEW 隔离区或 POISON 阻断区的最终状态。",
      '<button class="ghost" data-action="refresh-state">刷新状态</button>'
    )}
    ${renderError()}

    <section class="kb-tabs">
      ${tabs.map(([key, label, count, tabTone]) => `
        <button class="kb-tab ${state.kbTab === key ? "active" : ""} ${tabTone}" data-kb-tab="${key}">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(count)}</strong>
        </button>
      `).join("")}
    </section>

    <section class="document-grid">
      ${docs.length ? docs.map((doc) => renderDocumentCard(doc, tone)).join("") : `
        <div class="empty-state wide">
          <h3>当前区域暂无文档</h3>
          <p>可先前往“知识库安全准入”执行一次攻击样本扫描。</p>
        </div>
      `}
    </section>
  `;
}

function generationSummary(generation) {
  if (!generation || typeof generation !== "object") return { status: "—", text: "暂无生成结果" };
  const status = generation.status || generation.generation_status || generation.outcome || "—";
  const text =
    generation.text ||
    generation.answer ||
    generation.output ||
    generation.content ||
    generation.response ||
    generation.generated_text ||
    "";
  if (status === "NO_CONTEXT" && !text) return { status, text: "无可用安全上下文" };
  return { status, text: text || "生成结果未提供可展示文本" };
}

function renderRagColumn(title, subtitle, pathData, incomingId, protectedSide) {
  const chunks = Array.isArray(pathData?.chunks) ? pathData.chunks : [];
  const attackIndex = incomingId ? chunks.findIndex((x) => x.document_id === incomingId) : -1;
  const exposed = attackIndex >= 0;
  const generation = generationSummary(pathData?.generation);

  return `
    <article class="rag-column ${protectedSide ? "protected" : "vanilla"}">
      <div class="rag-column-header">
        <div>
          <span class="section-kicker">${protectedSide ? "PROTECTED PATH" : "BASELINE PATH"}</span>
          <h3>${escapeHtml(title)}</h3>
          <p>${escapeHtml(subtitle)}</p>
        </div>
        <div class="exposure-badge ${exposed ? "danger" : "safe"}">
          Attack Exposure = ${exposed ? "YES" : "NO"}
        </div>
      </div>

      ${incomingId ? `
        <div class="attack-rank ${exposed ? "danger" : "safe"}">
          ${exposed
            ? `攻击文档 ${escapeHtml(incomingId)} 出现在 Rank #${attackIndex + 1}`
            : `攻击文档 ${escapeHtml(incomingId)} 未出现在当前 Top-K`}
        </div>
      ` : ""}

      <div class="retrieval-status-row">
        <span>Retrieval Status</span>
        <strong>${escapeHtml(pathData?.retrieval_status || "—")}</strong>
      </div>

      <div class="topk-list">
        ${chunks.length ? chunks.map((chunk, index) => `
          <article class="topk-card ${chunk.document_id === incomingId ? "attack" : ""}">
            <div class="topk-head">
              <span class="rank">#${index + 1}</span>
              <strong>${escapeHtml(chunk.document_id)}</strong>
              <span class="score">${formatScore(chunk.score)}</span>
            </div>
            <p>${escapeHtml(shorten(chunk.text, 210))}</p>
            ${chunk.document_id === incomingId ? '<span class="attack-tag">攻击文档暴露</span>' : ""}
          </article>
        `).join("") : '<div class="empty-state">当前没有检索结果。</div>'}
      </div>

      <div class="generation-card">
        <div class="generation-card-head">
          <span>Generation</span>
          <strong>${escapeHtml(generation.status)}</strong>
        </div>
        <p>${escapeHtml(generation.text)}</p>
      </div>

      ${protectedSide ? `
        <div class="cic-card">
          <span>Context Integrity Checker</span>
          <strong>${escapeHtml(pathData?.cic?.status || pathData?.cic?.decision || (pathData?.cic ? "已执行" : "未触发 / 无结果"))}</strong>
        </div>
      ` : ""}
    </article>
  `;
}

function renderRagComparison() {
  const scenario = currentScenario();
  return `
    ${pageHeader(
      "RAG 安全对照",
      "同一问题、同一检索配置，对比 Vanilla RAG 与 ZhiYu Protected RAG 的攻击暴露差异。",
      '<button class="ghost" data-action="reset-demo">↻ 重置演示</button>'
    )}
    ${renderError()}

    <section class="panel rag-toolbar">
      <div class="rag-control">
        <label class="field-label" for="rag-scenario-select">演示场景</label>
        <select id="rag-scenario-select" class="scenario-select">
          ${state.scenarios.map((item) => `
            <option value="${escapeHtml(item.scenario_id)}" ${item.scenario_id === state.selectedScenarioId ? "selected" : ""}>
              ${escapeHtml(mechanismLabel(item.mechanism))} · ${escapeHtml(scenarioName(item))}
            </option>
          `).join("")}
        </select>
      </div>

      <div class="rag-control grow">
        <label class="field-label" for="rag-query">问题</label>
        <input id="rag-query" class="rag-query" value="${escapeHtml(state.ragQuery || scenario?.primary_question || "")}" />
      </div>

      <button class="primary run-button" data-action="run-rag" ${state.loading ? "disabled" : ""}>
        ${state.loading ? "正在运行安全对照…" : "运行安全对照"}
      </button>
    </section>

    ${renderFieldComparison(scenario)}

    ${state.ragResult ? `
      <section class="rag-grid">
        ${renderRagColumn("Vanilla RAG", "无安全准入保护", state.ragResult.vanilla, scenario?.incoming_document_id, false)}
        ${renderRagColumn("ZhiYu Protected RAG", "安全准入与上下文完整性检查启用", state.ragResult.protected, scenario?.incoming_document_id, true)}
      </section>
    ` : `
      <section class="panel rag-empty">
        <div class="rag-empty-icon">⇄</div>
        <h3>等待运行安全对照</h3>
        <p>运行后将并排展示 Vanilla 与 Protected 的真实 Top-K、生成结果以及攻击暴露情况。</p>
      </section>
    `}
  `;
}

function renderEvaluation() {
  return `
    ${pageHeader(
      "实验评估",
      "正式 Phase6 Evaluation 与当前 Live Demo 严格分离。",
      '<span class="official-badge">OFFICIAL EVALUATION</span>'
    )}

    <section class="metric-compare">
      <article class="metric-side vanilla">
        <span class="section-kicker">BASELINE</span>
        <h3>Vanilla RAG</h3>
        <div class="metric-row"><span>ASR</span><strong>50%</strong></div>
        <div class="metric-row"><span>DSR</span><strong>50%</strong></div>
        <div class="metric-row"><span>QA Accuracy</span><strong>100%</strong></div>
      </article>

      <div class="metric-vs">VS</div>

      <article class="metric-side protected">
        <span class="section-kicker">ZHIYU</span>
        <h3>Protected RAG</h3>
        <div class="metric-row"><span>ASR</span><strong>0%</strong></div>
        <div class="metric-row"><span>DSR</span><strong>100%</strong></div>
        <div class="metric-row"><span>QA Accuracy</span><strong>0%</strong></div>
      </article>
    </section>

    <section class="evaluation-grid">
      <article class="panel no-context-card">
        <span class="section-kicker">PROTECTED NO_CONTEXT</span>
        <strong>24 / 24</strong>
        <p>正式 generalization evaluation 中，Protected 路径全部进入 NO_CONTEXT。</p>
      </article>

      <article class="panel tradeoff-card">
        <span class="section-kicker">SECURITY–UTILITY TRADE-OFF</span>
        <h3>安全性与可用性的真实权衡</h3>
        <p>当前 Protected 模式采用保守 fail-closed 准入策略。严格安全准入降低攻击暴露，但也造成正常问答可用上下文不足。</p>
        <div class="warning-strip">
          Protected DSR = 100% 主要来自 NO_CONTEXT，不能归因于 CIC 单独实现完全防御。
        </div>
      </article>
    </section>
  `;
}

function renderApp() {
  if (state.loading && !state.backendState && state.scenarios.length === 0) {
    app.innerHTML = `
      <div class="initial-loading">
        <div class="loader"></div>
        <h2>正在加载 ZhiYu Demo…</h2>
        <p>正在获取场景、预设问题和安全知识库状态。</p>
      </div>
    `;
    return;
  }

  let html = "";
  if (state.currentPage === "overview") html = renderOverview();
  else if (state.currentPage === "admission") html = renderAdmission();
  else if (state.currentPage === "kb") html = renderKnowledgeBase();
  else if (state.currentPage === "rag") html = renderRagComparison();
  else if (state.currentPage === "eval") html = renderEvaluation();
  else html = renderOverview();

  app.innerHTML = `<div class="page-shell">${html}</div>`;
  bindDynamicEvents();
}

function bindDynamicEvents() {
  document.querySelector('[data-action="go-admission"]')?.addEventListener("click", () => navigate("admission"));

  document.querySelectorAll("[data-mechanism]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedMechanism = button.dataset.mechanism;
      const first = state.scenarios.find((x) => x.mechanism === state.selectedMechanism);
      if (first) {
        state.selectedScenarioId = first.scenario_id;
        state.ragQuery = first.primary_question || "";
      }
      state.scanResult = null;
      state.ragResult = null;
      renderApp();
    });
  });

  document.querySelector("#scenario-select")?.addEventListener("change", (event) => {
    state.selectedScenarioId = event.target.value;
    const scenario = currentScenario();
    state.ragQuery = scenario?.primary_question || "";
    state.scanResult = null;
    renderApp();
  });

  document.querySelector("#rag-scenario-select")?.addEventListener("change", (event) => {
    state.selectedScenarioId = event.target.value;
    const scenario = currentScenario();
    state.selectedMechanism = scenario?.mechanism || state.selectedMechanism;
    state.ragQuery = scenario?.primary_question || "";
    state.ragResult = null;
    renderApp();
  });

  document.querySelector("#rag-query")?.addEventListener("input", (event) => {
    state.ragQuery = event.target.value;
  });

  document.querySelector('[data-action="scan"]')?.addEventListener("click", handleScan);
  document.querySelector('[data-action="run-rag"]')?.addEventListener("click", handleRunRag);
  document.querySelectorAll('[data-action="reset-demo"]').forEach((button) => {
    button.addEventListener("click", handleReset);
  });
  document.querySelector('[data-action="refresh-state"]')?.addEventListener("click", handleRefreshState);

  document.querySelectorAll("[data-kb-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.kbTab = button.dataset.kbTab;
      renderApp();
    });
  });
}

async function handleScan() {
  const scenario = currentScenario();
  if (!scenario?.incoming_document_id) {
    state.error = "当前场景没有 Incoming Document，无需执行攻击扫描。";
    renderApp();
    return;
  }

  try {
    state.loading = true;
    state.error = "";
    state.scanResult = null;
    renderApp();

    const result = await apiPost("/api/scan", {
      document_id: scenario.incoming_document_id,
    });

    state.scanResult = result;
    await refreshBackendState();
    setToast(`扫描完成：${result.actual_decision}`);
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    renderApp();
  }
}

async function handleRunRag() {
  const scenario = currentScenario();
  const query = (state.ragQuery || "").trim();

  if (!scenario) {
    state.error = "请先选择演示场景。";
    renderApp();
    return;
  }
  if (!query) {
    state.error = "问题不能为空。";
    renderApp();
    return;
  }

  try {
    state.loading = true;
    state.error = "";
    state.ragResult = null;
    renderApp();

    state.ragResult = await apiPost("/api/run", {
      scenario_id: scenario.scenario_id,
      query_text: query,
    });
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    renderApp();
  }
}

async function handleReset() {
  try {
    state.loading = true;
    state.error = "";
    await apiPost("/api/reset", {});
    state.scanResult = null;
    state.ragResult = null;
    await refreshBackendState();
    setToast("演示环境已重置");
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    renderApp();
  }
}

async function handleRefreshState() {
  try {
    state.loading = true;
    state.error = "";
    await refreshBackendState();
    setToast("状态已刷新");
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    renderApp();
  }
}

navButtons.forEach((button) => {
  button.addEventListener("click", () => navigate(button.dataset.page));
});

updateNavActive();
loadInitialData();
