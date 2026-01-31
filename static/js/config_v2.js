/**
 * V2 配置中心（schema 驱动渲染）
 *
 * 目标：
 * - 左侧分组导航（llm/embeddings/gateway/...）
 * - 右侧自动生成表单（根据 schema 的 type/format）
 * - 支持高级 JSON 模式
 * - 支持测试连接、导入/导出
 */

let CFGV2 = {
  loaded: false,
  schema: null,
  configMasked: null,
  configUnmasked: null, // 仅用于 advanced 显示；不会直接展示敏感明文（后端默认 masked）
  activeSection: null,
  advancedMode: false,
};

const CFGV2_META = {
  llm: {
    base_url: {
      label: "LLM API Base URL",
      hint: "Gemini v1beta 的基址（第三方代理也应兼容 v1beta）。示例：https://generativelanguage.googleapis.com/v1beta",
      placeholder: "https://…/v1beta",
    },
    api_key: {
      label: "LLM API Key",
      hint: "保存后写入 `.env`（MOEBOT_LLM_API_KEY）。留空表示不修改。",
      placeholder: "已设置（留空保持不变）",
    },
    model: { label: "模型", hint: "例如 gemini-2.0-flash / gemini-2.0-pro", placeholder: "gemini-2.0-flash" },
    timeout: { label: "请求超时(秒)", hint: "单次请求超时上限", placeholder: "30" },
    max_tokens: { label: "最大输出 tokens", hint: "限制单次生成最大 tokens（仅配置，不代表一定生效）", placeholder: "8192" },
  },
  embeddings: {
    base_url: {
      label: "Embedding API Base URL",
      hint: "Embedding v1beta 的基址。示例：https://generativelanguage.googleapis.com/v1beta",
      placeholder: "https://…/v1beta",
    },
    api_key: {
      label: "Embedding API Key",
      hint: "保存后写入 `.env`（MOEBOT_EMBED_API_KEY）。留空表示不修改。",
      placeholder: "已设置（留空保持不变）",
    },
    model: { label: "Embedding 模型", hint: "例如 text-embedding-004", placeholder: "text-embedding-004" },
    dimensions: { label: "向量维度(可选)", hint: "留空使用模型默认维度", placeholder: "" },
    timeout: { label: "请求超时(秒)", hint: "单次请求超时上限", placeholder: "30" },
  },
  gateway: {
    host: { label: "监听地址", hint: "0.0.0.0=局域网可访问；127.0.0.1=仅本机", placeholder: "0.0.0.0" },
    port: { label: "监听端口", hint: "V2 Gateway 端口", placeholder: "8788" },
    cors_origins: { label: "CORS 允许源", hint: "一般留空即可；需要跨域时再填数组", placeholder: "[]" },
  },
  node_host: {
    host: { label: "监听地址", hint: "0.0.0.0=局域网可访问；127.0.0.1=仅本机", placeholder: "0.0.0.0" },
    port: { label: "监听端口", hint: "V2 Node-Host 端口", placeholder: "8789" },
    gateway_url: { label: "Gateway URL", hint: "Node-Host 连接 Gateway 的地址", placeholder: "http://127.0.0.1:8788" },
  },
  memory: {
    database_path: { label: "数据库路径", hint: "SQLite 文件路径", placeholder: "data/memory/moebot_v2.db" },
    chunk_size: { label: "分块大小", hint: "用于 embedding/索引的 chunk 大小", placeholder: "1200" },
    chunk_overlap: { label: "分块重叠", hint: "chunk overlap（必须小于 chunk_size）", placeholder: "200" },
    fts_enabled: { label: "FTS5 开关", hint: "是否开启全文索引", placeholder: "" },
  },
  context: {
    budget_chars: { label: "上下文预算(字符)", hint: "用于裁剪/压缩的预算上限", placeholder: "20000" },
    soft_trim_ratio: { label: "软裁剪阈值", hint: "coverage 低于该值开始裁剪（0~1）", placeholder: "0.7" },
    hard_clear_ratio: { label: "硬清空阈值", hint: "极端情况下清空 tool 输出（0~1）", placeholder: "0.9" },
  },
  security: {
    sandbox_enabled: { label: "Sandbox 开关", hint: "是否启用沙箱执行", placeholder: "" },
    sandbox_network: { label: "Sandbox 网络", hint: "是否允许沙箱访问网络（建议默认关闭）", placeholder: "" },
    tool_policy: { label: "工具策略", hint: "allow/deny 策略（JSON）", placeholder: "{}" },
    exec_approval: { label: "Exec 审批", hint: "是否需要审批高风险 exec", placeholder: "" },
  },
  paths: {
    skills_dir: { label: "skills 目录", hint: "默认相对工作目录", placeholder: "skills" },
    plugins_dir: { label: "plugins 目录", hint: "默认相对工作目录", placeholder: "plugins" },
    transcripts_dir: { label: "transcripts 目录", hint: "会话转录输出目录", placeholder: "data/transcripts" },
    media_dir: { label: "media 目录", hint: "媒体文件目录", placeholder: "media" },
  },
};

function _cfgv2El(id) {
  return document.getElementById(id);
}

function _cfgv2Toast(msg) {
  const wrap = _cfgv2El("cfgv2-toast");
  const text = _cfgv2El("cfgv2-toast-text");
  if (!wrap || !text) return;
  text.textContent = msg;
  wrap.classList.remove("hidden");
  setTimeout(() => wrap.classList.add("hidden"), 2800);
}

function _cfgv2SetStatus(text, kind = "idle") {
  const pill = _cfgv2El("cfgv2-status-pill");
  if (!pill) return;
  pill.textContent = text;
  pill.classList.remove("bg-gray-700", "bg-emerald-600", "bg-amber-600", "bg-rose-600");
  if (kind === "ok") pill.classList.add("bg-emerald-600");
  else if (kind === "warn") pill.classList.add("bg-amber-600");
  else if (kind === "err") pill.classList.add("bg-rose-600");
  else pill.classList.add("bg-gray-700");
}

function _cfgv2SectionLabel(section) {
  const map = {
    llm: ["fas fa-comment-dots", "LLM"],
    embeddings: ["fas fa-braille", "Embedding"],
    gateway: ["fas fa-network-wired", "Gateway"],
    node_host: ["fas fa-server", "Node-Host"],
    memory: ["fas fa-archive", "Memory"],
    context: ["fas fa-feather", "Context"],
    security: ["fas fa-shield-alt", "Security"],
    paths: ["fas fa-folder-open", "Paths"],
  };
  return map[section] || ["fas fa-sliders-h", section];
}

function _cfgv2Meta(section, key) {
  return (CFGV2_META[section] && CFGV2_META[section][key]) || null;
}

function _cfgv2DecodeJsonPointerToken(token) {
  return token.replace(/~1/g, "/").replace(/~0/g, "~");
}

function _cfgv2GetByPointer(root, pointer) {
  // pointer: "$defs/LLMConfig/properties/base_url"
  if (!pointer) return null;
  const parts = pointer.split("/").filter(Boolean).map(_cfgv2DecodeJsonPointerToken);
  let cur = root;
  for (const p of parts) {
    if (!cur || typeof cur !== "object" || !(p in cur)) return null;
    cur = cur[p];
  }
  return cur;
}

function _cfgv2ResolveSchema(node) {
  // resolve $ref + simplify anyOf(null)
  let cur = node;
  const seen = new Set();
  for (let i = 0; i < 16; i++) {
    if (!cur || typeof cur !== "object") break;
    if (cur.$ref && typeof cur.$ref === "string") {
      const ref = cur.$ref;
      if (seen.has(ref)) break;
      seen.add(ref);
      if (ref.startsWith("#/")) {
        const ptr = ref.slice(2);
        const next = _cfgv2GetByPointer(CFGV2.schema, ptr);
        if (!next) break;
        cur = next;
        continue;
      }
      break;
    }
    break;
  }

  if (cur && typeof cur === "object" && Array.isArray(cur.anyOf)) {
    // 常见：Optional[T] => anyOf([T, null])
    const desc = cur.description;
    const picked = cur.anyOf.find((x) => x && x.type !== "null") || cur.anyOf[0];
    const resolved = _cfgv2ResolveSchema(picked);
    if (desc && resolved && !resolved.description) resolved.description = desc;
    return resolved;
  }

  if (cur && typeof cur === "object" && Array.isArray(cur.allOf) && cur.allOf.length > 0) {
    // 常见：allOf([{$ref:...}])
    const desc = cur.description;
    const resolved = _cfgv2ResolveSchema(cur.allOf[0]);
    if (desc && resolved && !resolved.description) resolved.description = desc;
    return resolved;
  }

  return cur;
}

function _cfgv2BuildNav(sections) {
  const nav = _cfgv2El("cfgv2-nav");
  if (!nav) return;
  nav.innerHTML = "";

  sections.forEach((sec, idx) => {
    const [icon, label] = _cfgv2SectionLabel(sec);
    const btn = document.createElement("button");
    btn.className =
      "w-full text-left px-4 py-3 rounded-xl transition border border-transparent hover:border-gray-200 hover:bg-gray-50 flex items-center justify-between";
    btn.dataset.section = sec;

    btn.innerHTML = `
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-black text-white flex items-center justify-center shadow-sm">
          <i class="${icon}"></i>
        </div>
        <div>
          <div class="text-sm font-semibold text-gray-900">${htmlEscape(label)}</div>
          <div class="text-xs text-gray-500">${htmlEscape(sec)}</div>
        </div>
      </div>
      <i class="fas fa-angle-right text-gray-300"></i>
    `;
    btn.addEventListener("click", () => loadConfigV2Section(sec));
    nav.appendChild(btn);
  });
}

function _cfgv2MarkActiveNav(section) {
  document.querySelectorAll("#cfgv2-nav button[data-section]").forEach((b) => {
    const isActive = b.dataset.section === section;
    b.classList.toggle("bg-gray-900", isActive);
    b.classList.toggle("text-white", isActive);
    b.classList.toggle("hover:bg-gray-50", !isActive);
    // 反白内部文字
    b.querySelectorAll(".text-gray-900").forEach((x) => x.classList.toggle("text-white", isActive));
    b.querySelectorAll(".text-gray-500").forEach((x) => x.classList.toggle("text-gray-200", isActive));
    b.querySelectorAll(".text-gray-300").forEach((x) => x.classList.toggle("text-gray-200", isActive));
    // icon card 变色
    const iconCard = b.querySelector("div.w-9");
    if (iconCard) {
      iconCard.classList.toggle("bg-white", isActive);
      iconCard.classList.toggle("text-gray-900", isActive);
      iconCard.classList.toggle("bg-black", !isActive);
      iconCard.classList.toggle("text-white", !isActive);
    }
  });
}

function _cfgv2InputRow({ key, label, hint, inputHtml }) {
  const row = document.createElement("div");
  row.className = "grid grid-cols-1 md:grid-cols-12 gap-3 items-start";
  row.innerHTML = `
    <div class="md:col-span-4">
      <div class="text-sm font-semibold text-gray-900">${htmlEscape(label || key)}</div>
      <div class="text-xs text-gray-500 mt-1 leading-relaxed">${htmlEscape(hint || "")}</div>
    </div>
    <div class="md:col-span-8">
      ${inputHtml}
    </div>
  `;
  return row;
}

function _cfgv2RenderField(section, key, schema, value) {
  const normalized = _cfgv2ResolveSchema(schema);
  const type = normalized?.type;
  const format = normalized?.format;
  const meta = _cfgv2Meta(section, key);
  const description = meta?.hint || normalized?.description || "";

  const id = `cfgv2-${section}-${key}`;
  const name = `cfgv2.${section}.${key}`;

  // password: api_key 或 Secret
  const isSecret = key.toLowerCase().includes("api_key") || normalized?.writeOnly === true;
  const displayValue = isSecret && value === "****" ? "" : value;

  if (type === "boolean") {
    const checked = !!displayValue;
    const html = `
      <label class="inline-flex items-center gap-3 px-4 py-3 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 transition cursor-pointer">
        <input id="${id}" name="${name}" type="checkbox" class="h-5 w-5" ${checked ? "checked" : ""} />
        <span class="text-sm text-gray-800">启用</span>
      </label>
    `;
    return _cfgv2InputRow({ key, label: meta?.label || key, hint: description, inputHtml: html });
  }

  if (type === "integer" || type === "number") {
    const html = `
      <input id="${id}" name="${name}" type="number" value="${displayValue ?? ""}" placeholder="${htmlEscape(meta?.placeholder || "")}"
        class="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-400 transition"
      />
    `;
    return _cfgv2InputRow({ key, label: meta?.label || key, hint: description, inputHtml: html });
  }

  if (type === "array") {
    const v = Array.isArray(displayValue) ? displayValue : [];
    const html = `
      <textarea id="${id}" name="${name}" class="w-full h-28 font-mono text-sm px-4 py-3 rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-400 transition"
        placeholder="${htmlEscape(meta?.placeholder || "用 JSON 数组格式输入，例如 [\\\"a\\\", \\\"b\\\"]")}"
      >${htmlEscape(JSON.stringify(v, null, 2))}</textarea>
    `;
    return _cfgv2InputRow({
      key,
      label: meta?.label || key,
      hint: description || "数组字段（JSON 格式）",
      inputHtml: html,
    });
  }

  // object：在这一版里不做深层递归，直接 JSON textarea（避免过度复杂）
  if (type === "object") {
    const html = `
      <textarea id="${id}" name="${name}" class="w-full h-40 font-mono text-sm px-4 py-3 rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-400 transition"
        placeholder="${htmlEscape(meta?.placeholder || "用 JSON 对象格式输入")}"
      >${htmlEscape(JSON.stringify(displayValue ?? {}, null, 2))}</textarea>
    `;
    return _cfgv2InputRow({
      key,
      label: meta?.label || key,
      hint: description || "对象字段（JSON 格式）",
      inputHtml: html,
    });
  }

  // string（默认）
  const inputType = isSecret ? "password" : "text";
  const placeholder = meta?.placeholder || (format === "uri" ? "https://..." : isSecret ? "留空表示不修改" : "");

  const html = `
    <div class="relative">
      <input id="${id}" name="${name}" type="${inputType}" value="${htmlEscape(displayValue ?? "")}"
        placeholder="${htmlEscape(placeholder)}"
        class="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-400 transition ${isSecret ? "pr-12" : ""}"
      />
      ${
        isSecret
          ? `<button type="button" data-toggle="${id}" class="absolute right-2 top-1/2 -translate-y-1/2 w-9 h-9 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 transition">
              <i class="fas fa-eye text-gray-600"></i>
            </button>`
          : ""
      }
    </div>
  `;
  return _cfgv2InputRow({ key, label: meta?.label || key, hint: description, inputHtml: html });
}

function _cfgv2BindSecretToggles(rootEl) {
  rootEl.querySelectorAll("button[data-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.toggle;
      const input = document.getElementById(id);
      if (!input) return;
      input.type = input.type === "password" ? "text" : "password";
      btn.querySelector("i").className =
        input.type === "password" ? "fas fa-eye text-gray-600" : "fas fa-eye-slash text-gray-600";
    });
  });
}

function _cfgv2CollectSection(section) {
  const schema = _cfgv2ResolveSchema(CFGV2.schema?.properties?.[section]);
  const props = schema?.properties || {};
  const out = {};

  Object.keys(props).forEach((key) => {
    const fieldSchema = _cfgv2ResolveSchema(props[key]);
    const id = `cfgv2-${section}-${key}`;
    const el = document.getElementById(id);
    if (!el) return;

    const isSecret = key.toLowerCase().includes("api_key") || fieldSchema?.writeOnly === true;
    const t = fieldSchema?.type;
    if (t === "boolean") {
      out[key] = !!el.checked;
      return;
    }
    if (t === "integer") {
      out[key] = el.value === "" ? null : parseInt(el.value, 10);
      return;
    }
    if (t === "number") {
      out[key] = el.value === "" ? null : Number(el.value);
      return;
    }
    if (t === "array" || t === "object") {
      const raw = el.value || "";
      try {
        out[key] = raw.trim() ? JSON.parse(raw) : (t === "array" ? [] : {});
      } catch (e) {
        throw new Error(`字段 ${section}.${key} JSON 解析失败`);
      }
      return;
    }

    if (isSecret) {
      const v = (el.value || "").trim();
      // 留空 = 不修改；"****" = 遮蔽值，不允许覆盖
      if (!v || v === "****") return;
      out[key] = v;
      return;
    }

    out[key] = el.value;
  });

  return out;
}

async function loadConfigV2() {
  try {
    _cfgv2SetStatus("加载中…");
    CFGV2.schema = await API.getConfigV2Schema();
    CFGV2.configMasked = await API.getConfigV2(true);
    CFGV2.loaded = true;

    const sections = Object.keys(CFGV2.schema?.properties || {});
    _cfgv2BuildNav(sections);
    _cfgv2SetStatus("已加载", "ok");

    // 默认选第一个
    if (sections.length > 0) {
      await loadConfigV2Section(sections[0]);
    }
  } catch (e) {
    console.error(e);
    _cfgv2SetStatus("加载失败", "err");
    _cfgv2Toast("V2 配置加载失败：后端 /api/v2/config 可能未启用");
  }
}

async function loadConfigV2Section(section) {
  if (!CFGV2.loaded) return;
  CFGV2.activeSection = section;
  _cfgv2MarkActiveNav(section);

  const title = _cfgv2El("cfgv2-panel-title");
  const subtitle = _cfgv2El("cfgv2-panel-subtitle");
  if (title) title.textContent = `${section}`;
  if (subtitle) subtitle.textContent = "按字段编辑（保存时后端会校验并落盘）";

  const form = _cfgv2El("cfgv2-form");
  const adv = _cfgv2El("cfgv2-advanced");
  const advEditor = _cfgv2El("cfgv2-advanced-editor");
  if (!form || !adv || !advEditor) return;

  // 切回表单模式
  CFGV2.advancedMode = false;
  adv.classList.add("hidden");
  form.classList.remove("hidden");

  // 取该 section 的 schema + value
  const schema = _cfgv2ResolveSchema(CFGV2.schema?.properties?.[section]);
  const props = schema?.properties || {};
  const value = (CFGV2.configMasked || {})[section] || {};

  form.innerHTML = "";

  // 顶部小提示条（有点“编辑器”感）
  const info = document.createElement("div");
  info.className =
    "p-4 rounded-2xl border border-gray-200 bg-gradient-to-r from-amber-50 via-white to-emerald-50";
  info.innerHTML = `
    <div class="flex items-start justify-between gap-3">
      <div>
        <div class="text-sm font-semibold text-gray-900">你正在编辑：${htmlEscape(section)}</div>
        <div class="text-xs text-gray-600 mt-1">建议：先填 base_url / model，再填 API Key，最后点“测试连接”。</div>
      </div>
      <div class="text-xs text-gray-500">schema 驱动</div>
    </div>
  `;
  form.appendChild(info);

  Object.keys(props).forEach((k) => {
    const row = _cfgv2RenderField(section, k, props[k], value[k]);
    form.appendChild(row);
  });

  _cfgv2BindSecretToggles(form);

  // 高级编辑器内容
  advEditor.value = JSON.stringify(value, null, 2);
}

async function saveConfigV2ActiveSection() {
  const sec = CFGV2.activeSection;
  if (!sec) return;
  try {
    if (CFGV2.advancedMode) {
      const advEditor = _cfgv2El("cfgv2-advanced-editor");
      const raw = advEditor?.value || "";
      const obj = raw.trim() ? JSON.parse(raw) : {};
      // 遮蔽值不要覆盖真实 key；留空也不覆盖
      if (obj && typeof obj === "object") {
        for (const k of Object.keys(obj)) {
          if (String(k).toLowerCase().includes("api_key")) {
            const v = obj[k];
            if (!v || v === "****") delete obj[k];
          }
        }
      }
      const res = await API.patchConfigV2Section(sec, obj);
      if (!res.success) throw new Error(res.message || "保存失败");
    } else {
      const payload = _cfgv2CollectSection(sec);
      const res = await API.patchConfigV2Section(sec, payload);
      if (!res.success) throw new Error(res.message || "保存失败");
    }

    CFGV2.configMasked = await API.getConfigV2(true);
    _cfgv2Toast("保存成功");
  } catch (e) {
    console.error(e);
    _cfgv2Toast(`保存失败：${e?.message || e}`);
  }
}

function _cfgv2OpenImport() {
  const modal = _cfgv2El("cfgv2-import-modal");
  const editor = _cfgv2El("cfgv2-import-editor");
  if (!modal || !editor) return;
  editor.value = "";
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function _cfgv2CloseImport() {
  const modal = _cfgv2El("cfgv2-import-modal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

async function _cfgv2DoImport() {
  const editor = _cfgv2El("cfgv2-import-editor");
  if (!editor) return;
  try {
    const raw = editor.value || "";
    let obj = raw.trim() ? JSON.parse(raw) : {};
    if (obj && obj.config) obj = obj.config;
    const res = await API.importConfigV2(obj);
    if (!res.success) throw new Error(res.message || "导入失败");
    CFGV2.configMasked = await API.getConfigV2(true);
    if (CFGV2.activeSection) await loadConfigV2Section(CFGV2.activeSection);
    _cfgv2Toast("导入成功");
    _cfgv2CloseImport();
  } catch (e) {
    console.error(e);
    _cfgv2Toast(`导入失败：${e?.message || e}`);
  }
}

async function _cfgv2DoExport() {
  try {
    const res = await API.exportConfigV2();
    showDetail("V2 配置导出（YAML 非敏感 + masked）", res);
  } catch (e) {
    console.error(e);
    _cfgv2Toast("导出失败");
  }
}

async function _cfgv2DoTest(section) {
  try {
    const res = await API.testConfigV2(section);
    if (res.ok) _cfgv2Toast(`${section} 可达（HTTP ${res.status_code ?? "-" }）`);
    else _cfgv2Toast(`${section} 不可达：${res.message || "error"}`);
  } catch (e) {
    console.error(e);
    _cfgv2Toast("测试失败");
  }
}

function _cfgv2ToggleAdvanced() {
  const form = _cfgv2El("cfgv2-form");
  const adv = _cfgv2El("cfgv2-advanced");
  if (!form || !adv) return;
  CFGV2.advancedMode = !CFGV2.advancedMode;
  if (CFGV2.advancedMode) {
    form.classList.add("hidden");
    adv.classList.remove("hidden");
  } else {
    adv.classList.add("hidden");
    form.classList.remove("hidden");
  }
}

// 在 main.js 的导航切换里会调用
async function loadConfigV2Page() {
  if (CFGV2.loaded) return;
  await loadConfigV2();
}

// 绑定按钮（DOMContentLoaded 时执行一次）
document.addEventListener("DOMContentLoaded", () => {
  const btnRefresh = _cfgv2El("cfgv2-btn-refresh");
  const btnSave = _cfgv2El("cfgv2-btn-save");
  const btnAdv = _cfgv2El("cfgv2-btn-advanced");
  const btnTestLlm = _cfgv2El("cfgv2-btn-test-llm");
  const btnTestEmb = _cfgv2El("cfgv2-btn-test-emb");
  const btnExport = _cfgv2El("cfgv2-btn-export");
  const btnImport = _cfgv2El("cfgv2-btn-import");

  if (btnRefresh) btnRefresh.addEventListener("click", () => loadConfigV2());
  if (btnSave) btnSave.addEventListener("click", () => saveConfigV2ActiveSection());
  if (btnAdv) btnAdv.addEventListener("click", () => _cfgv2ToggleAdvanced());
  if (btnTestLlm) btnTestLlm.addEventListener("click", () => _cfgv2DoTest("llm"));
  if (btnTestEmb) btnTestEmb.addEventListener("click", () => _cfgv2DoTest("embeddings"));
  if (btnExport) btnExport.addEventListener("click", () => _cfgv2DoExport());
  if (btnImport) btnImport.addEventListener("click", () => _cfgv2OpenImport());

  const modal = _cfgv2El("cfgv2-import-modal");
  const close = _cfgv2El("cfgv2-import-close");
  const cancel = _cfgv2El("cfgv2-import-cancel");
  const confirm = _cfgv2El("cfgv2-import-confirm");
  if (close) close.addEventListener("click", () => _cfgv2CloseImport());
  if (cancel) cancel.addEventListener("click", () => _cfgv2CloseImport());
  if (confirm) confirm.addEventListener("click", () => _cfgv2DoImport());
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) _cfgv2CloseImport();
    });
  }

  // 纯 V2 配置中心模式：页面加载后自动初始化
  const root = _cfgv2El("config-v2");
  if (root && !CFGV2.loaded) {
    loadConfigV2();
  }
});

