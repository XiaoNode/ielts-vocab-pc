<template>
  <div class="app" :class="{ 'sidebar-open': sidebarOpen }">
    <aside class="sidebar">
      <div class="logo">
        <span class="logo-icon">英</span>
        <div class="logo-text">
          <div class="logo-title">雅思斩词</div>
          <div class="logo-sub">IELTS Vocab · PC</div>
        </div>
      </div>

      <nav class="nav">
        <button class="nav-item" :class="{ active: view === 'learn' }" @click="go('learn')">
          <span class="nav-ic">▶</span> 今日学习
          <span v-if="dueCount > 0" class="badge">{{ dueCount }}</span>
        </button>
        <button class="nav-item" :class="{ active: view === 'review' }" @click="go('review')">
          <span class="nav-ic">↻</span> 复习巩固
        </button>
        <button class="nav-item" :class="{ active: view === 'browse' }" @click="go('browse')">
          <span class="nav-ic">📖</span> 词库浏览
        </button>
        <button class="nav-item" :class="{ active: view === 'stats' }" @click="go('stats')">
          <span class="nav-ic">📊</span> 学习统计
        </button>
        <button class="nav-item" :class="{ active: view === 'settings' }" @click="go('settings')">
          <span class="nav-ic">⚙</span> 设置与迁移
        </button>
      </nav>

      <div class="sidebar-foot">
        <div class="mini-stats">
          <div class="ms-row"><span>今日已学</span><b>{{ todayLearned }}</b></div>
          <div class="ms-row"><span>已掌握</span><b>{{ stats.mastered }}</b></div>
        </div>
      </div>
    </aside>

    <main class="main">
      <section v-if="view === 'learn'" class="view learn-view">
        <div class="topbar">
          <button class="menu-btn" @click="sidebarOpen = !sidebarOpen">☰</button>
          <h1>今日学习</h1>
          <div class="topbar-right">
            <span class="accent-switch">
              <button :class="{ on: accent === 'us' }" @click="setAccent('us')">🇺🇸 美式</button>
              <button :class="{ on: accent === 'gb' }" @click="setAccent('gb')">🇬🇧 英式</button>
            </span>
          </div>
        </div>

        <div v-if="!loaded" class="loading">词库加载中…</div>

        <div v-else-if="currentWord" class="study-area">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: sessionProgress + '%' }"></div>
          </div>
          <div class="session-info">
            <span>第 {{ sessionIndex + 1 }} / {{ sessionQueue.length }} 词</span>
            <span>· 本组新学 {{ sessionNew }} 词</span>
          </div>

          <div class="card">
            <div class="word-head">
              <div class="word">{{ currentWord.word }}</div>
              <div class="phonetic">{{ currentWord.phonetic }}</div>
              <div class="speak-btns">
                <button class="btn-speak" @click="playWord('us')">🔊 美</button>
                <button class="btn-speak" @click="playWord('gb')">🔊 英</button>
              </div>
            </div>

            <div v-if="revealed" class="word-body">
              <div class="translation">{{ currentWord.translation }}</div>
              <div v-if="currentWord.pos" class="pos-tag">{{ currentWord.pos }}</div>

              <div v-if="currentWord.example" class="example-block">
                <div class="example-label">例句</div>
                <div class="example-en">
                  <span
                    v-for="(tok, i) in exampleTokens"
                    :key="i"
                    class="ex-token"
                    :class="{ hl: tok.clean === currentWord.word.toLowerCase() }"
                    @mouseenter="showTokenTip(tok, $event)"
                    @mouseleave="hideTokenTip"
                    @click="playToken(tok)"
                  >{{ tok.text }}</span>
                </div>
                <div class="example-cn">{{ currentWord.example_cn }}</div>
              </div>

              <div class="spell-check">
                <div class="spell-label">拼写检查（可选，验证是否真正记住）</div>
                <input
                  v-model="spellInput"
                  class="spell-input"
                  placeholder="输入单词拼写"
                  @keyup.enter="checkSpell"
                />
                <button class="btn" @click="checkSpell">检查拼写</button>
                <div v-if="spellResult" class="spell-result" :class="spellOk ? 'ok' : 'bad'">
                  {{ spellResult }}
                </div>
              </div>
            </div>

            <div v-if="!revealed" class="reveal-zone">
              <p class="hint">先回忆这个词的意思，再按空格键或点击下方查看</p>
              <button class="btn btn-primary btn-lg" @click="reveal">显示释义 (空格)</button>
            </div>
            <div v-else class="mark-zone">
              <button class="mark-btn hu" @click="mark('hu')">
                <div class="mark-title">糊</div>
                <div class="mark-desc">眼熟想不起来</div>
              </button>
              <button class="mark-btn shi" @click="mark('shi')">
                <div class="mark-title">识</div>
                <div class="mark-desc">认识但拼写不流畅</div>
              </button>
              <button class="mark-btn zhan" @click="mark('zhan')">
                <div class="mark-title">斩</div>
                <div class="mark-desc">完全熟记</div>
              </button>
            </div>
          </div>
        </div>

        <div v-else class="done">
          <div class="done-icon">🎉</div>
          <h2>今日任务完成！</h2>
          <p>今天已学习 {{ todayLearned }} 个单词</p>
          <button class="btn btn-primary" @click="startNewSession">再来一组</button>
          <button class="btn" @click="go('stats')">查看统计</button>
        </div>
      </section>

      <section v-else-if="view === 'review'" class="view">
        <div class="topbar">
          <button class="menu-btn" @click="sidebarOpen = !sidebarOpen">☰</button>
          <h1>复习巩固</h1>
        </div>
        <div class="review-list">
          <p class="hint" v-if="dueWords.length === 0">暂无到期需要复习的单词 🎉</p>
          <div v-for="w in dueWords" :key="w.word" class="review-item" @click="openReview(w)">
            <div class="ri-word">{{ w.word }}</div>
            <div class="ri-trans">{{ shortTrans(w.translation) }}</div>
            <div class="ri-mark" :class="w.rec?.mark">{{ markLabel(w.rec?.mark) }}</div>
          </div>
        </div>
      </section>

      <section v-else-if="view === 'browse'" class="view">
        <div class="topbar">
          <button class="menu-btn" @click="sidebarOpen = !sidebarOpen">☰</button>
          <h1>词库浏览</h1>
        </div>
        <div class="browse-toolbar">
          <input v-model="searchQuery" class="search-input" placeholder="搜索单词或释义…" @input="filterBrowse" />
          <div class="filter-group">
            <button
              v-for="f in markFilters"
              :key="f.key"
              class="filter-chip"
              :class="{ on: activeMarkFilter === f.key }"
              @click="setMarkFilter(f.key)"
            >{{ f.label }}</button>
          </div>
        </div>
        <div class="word-grid">
          <div
            v-for="w in filteredWords"
            :key="w.word"
            class="word-cell"
            :class="'mark-' + (progress[w.word]?.mark || 'none')"
            @click="openWordDetail(w)"
          >
            <div class="wc-word">{{ w.word }}</div>
            <div class="wc-phon">{{ w.phonetic }}</div>
            <div class="wc-trans">{{ shortTrans(w.translation) }}</div>
          </div>
          <div v-if="filteredWords.length === 0" class="hint">无匹配结果</div>
        </div>
      </section>

      <section v-else-if="view === 'stats'" class="view">
        <div class="topbar">
          <button class="menu-btn" @click="sidebarOpen = !sidebarOpen">☰</button>
          <h1>学习统计</h1>
        </div>
        <div class="stats-grid">
          <div class="stat-card"><div class="sc-val">{{ stats.total }}</div><div class="sc-label">词库总量</div></div>
          <div class="stat-card"><div class="sc-val">{{ stats.learning }}</div><div class="sc-label">学习中</div></div>
          <div class="stat-card"><div class="sc-val accent">{{ stats.mastered }}</div><div class="sc-label">已掌握</div></div>
          <div class="stat-card"><div class="sc-val accent">{{ stats.verified }}</div><div class="sc-label">已验证</div></div>
        </div>
        <div class="mark-breakdown">
          <h3>标记分布</h3>
          <div class="mb-bar">
            <div class="mb-seg zhan" :style="{ width: pct(stats.markCount.zhan) + '%' }" :title="'斩 ' + stats.markCount.zhan"></div>
            <div class="mb-seg shi" :style="{ width: pct(stats.markCount.shi) + '%' }" :title="'识 ' + stats.markCount.shi"></div>
            <div class="mb-seg hu" :style="{ width: pct(stats.markCount.hu) + '%' }" :title="'糊 ' + stats.markCount.hu"></div>
            <div class="mb-seg none" :style="{ width: pct(stats.markCount.none) + '%' }" :title="'未标记 ' + stats.markCount.none"></div>
          </div>
          <div class="mb-legend">
            <span><i class="dot zhan"></i>斩 {{ stats.markCount.zhan }}</span>
            <span><i class="dot shi"></i>识 {{ stats.markCount.shi }}</span>
            <span><i class="dot hu"></i>糊 {{ stats.markCount.hu }}</span>
            <span><i class="dot none"></i>未标记 {{ stats.markCount.none }}</span>
          </div>
        </div>
      </section>

      <section v-else-if="view === 'settings'" class="view">
        <div class="topbar">
          <button class="menu-btn" @click="sidebarOpen = !sidebarOpen">☰</button>
          <h1>设置与迁移</h1>
        </div>
        <div class="settings-block">
          <h3>学习设置</h3>
          <label class="setting-row">
            <span>每日新学目标</span>
            <select v-model.number="dailyTarget">
              <option :value="10">10 词</option>
              <option :value="20">20 词</option>
              <option :value="30">30 词</option>
              <option :value="50">50 词</option>
            </select>
          </label>
          <label class="setting-row">
            <span>默认发音</span>
            <select v-model="accent">
              <option value="us">美式 (en-US)</option>
              <option value="gb">英式 (en-GB)</option>
            </select>
          </label>
        </div>

        <div class="settings-block">
          <h3>数据迁移</h3>
          <p class="hint">学习进度仅保存在本机浏览器。可导出 JSON 备份，在另一台电脑导入后无缝继续。</p>
          <div class="btn-row">
            <button class="btn" @click="doExport">导出进度 (JSON)</button>
            <button class="btn" @click="doImport">导入进度</button>
            <button class="btn btn-danger" @click="doReset">重置全部进度</button>
          </div>
          <textarea
            v-if="showImport"
            class="import-area"
            placeholder="粘贴导出的 JSON 内容…"
          ></textarea>
          <div class="btn-row" v-if="showImport">
            <button class="btn btn-primary" @click="confirmImport">确认导入</button>
            <button class="btn" @click="showImport = false">取消</button>
          </div>
          <div v-if="importMsg" class="import-msg" :class="importOk ? 'ok' : 'bad'">{{ importMsg }}</div>
        </div>

        <div class="settings-block">
          <h3>关于词库</h3>
          <p class="hint">词库基于 ECDICT（MIT 许可）筛选，例句来自 Tatoeba（CC BY 2.0 FR）。</p>
          <p class="hint">发音优先使用本地音频，缺失时回退到系统语音合成（需系统 TTS 支持）。</p>
        </div>
      </section>

      <div v-if="detailWord" class="modal-mask" @click.self="detailWord = null">
        <div class="modal">
          <button class="modal-close" @click="detailWord = null">✕</button>
          <div class="word-head">
            <div class="word">{{ detailWord.word }}</div>
            <div class="phonetic">{{ detailWord.phonetic }}</div>
            <div class="speak-btns">
              <button class="btn-speak" @click="playWord('us', detailWord.word)">🔊 美</button>
              <button class="btn-speak" @click="playWord('gb', detailWord.word)">🔊 英</button>
            </div>
          </div>
          <div class="translation">{{ detailWord.translation }}</div>
          <div v-if="detailWord.example" class="example-block">
            <div class="example-label">例句</div>
            <div class="example-en">
              <span v-for="(tok, i) in detailTokens" :key="i" class="ex-token"
                @mouseenter="showTokenTip(tok, $event)" @mouseleave="hideTokenTip"
                @click="playToken(tok)">{{ tok.text }}</span>
            </div>
            <div class="example-cn">{{ detailWord.example_cn }}</div>
          </div>
          <div class="detail-marks">
            <span>当前标记：<b :class="detailWord?.rec?.mark">{{ markLabel(detailWord.rec?.mark) }}</b></span>
            <button class="mark-btn mini hu" @click="markWordInDetail('hu')">糊</button>
            <button class="mark-btn mini shi" @click="markWordInDetail('shi')">识</button>
            <button class="mark-btn mini zhan" @click="markWordInDetail('zhan')">斩</button>
          </div>
        </div>
      </div>

      <div v-if="tokenTip" class="token-tip" :style="tipStyle">
        <div class="tip-word">{{ tokenTip.clean }}</div>
        <div class="tip-actions">
          <button @click="playToken(tokenTip)">🔊 发音</button>
          <button @click="lookupToken(tokenTip)">查词</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import { speak, stopSpeak } from "./audio.js";
import lexiconBundle from "./lexicon-data.js";
import {
  loadProgress, saveProgress, applyResult, computeStats,
  exportProgress, importProgress, todayStr,
} from "./store.js";

const SESSION_SIZE = 10;

export default {
  name: "App",
  setup() {
    // ---- 基础状态 ----
    const view = ref("learn");
    const sidebarOpen = ref(false);
    const accent = ref(localStorage.getItem("ielts-accent") || "us");
    const dailyTarget = ref(parseInt(localStorage.getItem("ielts-daily") || "20", 10));

    const lexicon = ref([]);
    const lexiconMeta = ref(null);
    const loaded = ref(false);
    const progress = ref({});

    // ---- 学习会话状态 ----
    const sessionQueue = ref([]);
    const sessionIndex = ref(0);
    const sessionNew = ref(0);
    const revealed = ref(false);
    const spellInput = ref("");
    const spellResult = ref("");
    const spellOk = ref(false);

    // ---- 浏览/详情状态 ----
    const searchQuery = ref("");
    const activeMarkFilter = ref("all");
    const detailWord = ref(null);
    const tokenTip = ref(null);
    const tipStyle = ref({});
    const showImport = ref(false);
    const importMsg = ref("");
    const importOk = ref(false);

    const markFilters = [
      { key: "all", label: "全部" },
      { key: "zhan", label: "斩" },
      { key: "shi", label: "识" },
      { key: "hu", label: "糊" },
      { key: "none", label: "未标记" },
    ];

    // ---- 计算属性 ----
    const stats = computed(() => {
      const s = computeStats(progress.value);
      // total 口径修正：显示词库总量（而非仅有学习记录的词数）
      s.total = lexicon.value.length;
      s.newCount = s.total - s.learning - s.mastered;
      return s;
    });
    const todayLearned = computed(() => {
      const day = todayStr();
      let n = 0;
      for (const w of Object.values(progress.value)) {
        if (w.lastResultDay === day) n++;
      }
      return n;
    });
    const dueWords = computed(() => {
      const now = Date.now();
      const list = [];
      for (const word of lexicon.value) {
        const rec = progress.value[word.word];
        if (rec && rec.dueAt && rec.dueAt <= now) {
          list.push({ ...word, rec });
        }
      }
      return list;
    });
    const dueCount = computed(() => dueWords.value.length);
    const currentWord = computed(() => sessionQueue.value[sessionIndex.value] || null);
    const sessionProgress = computed(() => {
      if (!sessionQueue.value.length) return 0;
      return Math.round((sessionIndex.value / sessionQueue.value.length) * 100);
    });
    const exampleTokens = computed(() => tokenize(currentWord.value?.example || ""));
    const detailTokens = computed(() => tokenize(detailWord.value?.example || ""));
    const filteredWords = computed(() => {
      let list = lexicon.value;
      if (activeMarkFilter.value !== "all") {
        list = list.filter((w) => (progress.value[w.word]?.mark || "none") === activeMarkFilter.value);
      }
      if (searchQuery.value.trim()) {
        const q = searchQuery.value.trim().toLowerCase();
        list = list.filter((w) =>
          w.word.toLowerCase().includes(q) || w.translation.toLowerCase().includes(q)
        );
      }
      return list.slice(0, 500);
    });

    // ---- 工具函数 ----
    function tokenize(sentence) {
      if (!sentence) return [];
      const parts = sentence.split(/(\s+)/);
      const toks = [];
      for (const p of parts) {
        if (!p.trim()) {
          toks.push({ text: p, clean: "" });
          continue;
        }
        const clean = p.replace(/[^A-Za-z']/g, "").toLowerCase();
        toks.push({ text: p, clean });
      }
      return toks;
    }
    function shortTrans(t) {
      if (!t) return "";
      const line = t.split("\n")[0];
      return line.length > 30 ? line.slice(0, 30) + "…" : line;
    }
    function markLabel(m) {
      if (m === "zhan") return "斩";
      if (m === "shi") return "识";
      if (m === "hu") return "糊";
      return "未标记";
    }
    function pct(n) {
      const total = stats.value.total;
      if (!total) return 0;
      return Math.round((n / total) * 100);
    }

    // ---- 词库加载 ----
    async function loadLexicon() {
      try {
        // 词库已内联进 JS（lexicon-data.js），无需 fetch，file:// 双击直开也能用
        const data = lexiconBundle;
        lexicon.value = data.words || [];
        lexiconMeta.value = data.manifest || null;
        progress.value = loadProgress();
        loaded.value = true;
      } catch (e) {
        console.error("loadLexicon failed", e);
        // 降级：空词库
        lexicon.value = [];
        lexiconMeta.value = null;
        loaded.value = true;
      }
    }

    // ---- 学习会话 ----
    function startNewSession() {
      const now = Date.now();
      const day = todayStr();
      const learnedToday = new Set();
      for (const [word, rec] of Object.entries(progress.value)) {
        if (rec && rec.lastResultDay === day) learnedToday.add(word);
      }
      // 优先到期复习词，其次新词
      const due = [];
      const fresh = [];
      for (const w of lexicon.value) {
        const rec = progress.value[w.word];
        if (rec && rec.dueAt && rec.dueAt <= now) due.push(w);
        else if (!rec || rec.status === "new") fresh.push(w);
      }
      const queue = [...due, ...fresh].filter((w) => !learnedToday.has(w.word) || (progress.value[w.word]?.dueAt && progress.value[w.word].dueAt <= now));
      sessionQueue.value = queue.slice(0, Math.max(SESSION_SIZE, dailyTarget.value));
      sessionIndex.value = 0;
      sessionNew.value = 0;
      revealed.value = false;
      spellInput.value = "";
      spellResult.value = "";
    }

    function reveal() {
      revealed.value = true;
      nextTick(() => {
        if (currentWord.value) {
          const el = document.querySelector(".spell-input");
          if (el) el.focus();
        }
      });
    }

    function playWord(acc, word) {
      const w = word || currentWord.value?.word;
      if (w) speak(w, acc, w);
    }

    function checkSpell() {
      const w = currentWord.value;
      if (!w) return;
      const input = spellInput.value.trim().toLowerCase();
      const target = w.word.toLowerCase();
      if (!input) return;
      if (input === target) {
        spellOk.value = true;
        spellResult.value = "✓ 拼写正确！";
      } else {
        spellOk.value = false;
        spellResult.value = `✗ 拼写错误，正确为：${w.word}`;
      }
    }

    function mark(markType) {
      const w = currentWord.value;
      if (!w) return;
      const rec = progress.value[w.word] || null;
      const correct = markType !== "hu"; // 糊=想不起来；识/斩=认识
      progress.value[w.word] = applyResult(rec, markType, correct);
      saveProgress(progress.value);
      // 前进
      sessionIndex.value++;
      revealed.value = false;
      spellInput.value = "";
      spellResult.value = "";
      spellOk.value = false;
      if (sessionIndex.value >= sessionQueue.value.length) {
        sessionQueue.value = [];
      }
    }

    // ---- 单词详情 ----
    function openWordDetail(w) {
      detailWord.value = { ...w, rec: progress.value[w.word] || null };
    }
    function openReview(w) {
      openWordDetail(w);
    }
    function markWordInDetail(markType) {
      const w = detailWord.value;
      if (!w) return;
      const rec = progress.value[w.word] || null;
      progress.value[w.word] = applyResult(rec, markType, markType !== "hu");
      saveProgress(progress.value);
      detailWord.value = { ...w, rec: progress.value[w.word] };
    }

    // ---- 例句 token 交互 ----
    function showTokenTip(tok, event) {
      if (!tok.clean) {
        tokenTip.value = null;
        return;
      }
      tokenTip.value = tok;
      const rect = event.target.getBoundingClientRect();
      tipStyle.value = {
        left: rect.left + "px",
        top: (rect.bottom + 6) + "px",
      };
    }
    function hideTokenTip() {
      tokenTip.value = null;
    }
    function playToken(tok) {
      if (tok.clean) speak(tok.clean, accent.value, tok.clean);
    }
    function lookupToken(tok) {
      if (!tok.clean) return;
      const found = lexicon.value.find((w) => w.word.toLowerCase() === tok.clean);
      if (found) {
        detailWord.value = { ...found, rec: progress.value[found.word] || null };
        tokenTip.value = null;
      }
    }

    // ---- 浏览筛选 ----
    function filterBrowse() {
      // 计算属性已响应 searchQuery / activeMarkFilter
    }
    function setMarkFilter(key) {
      activeMarkFilter.value = key;
    }

    // ---- 设置/迁移 ----
    function setAccent(a) {
      accent.value = a;
      localStorage.setItem("ielts-accent", a);
    }
    function doExport() {
      const json = exportProgress(progress.value, lexiconMeta.value);
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ielts-vocab-backup-${todayStr()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
    function doImport() {
      showImport.value = true;
      importMsg.value = "";
      nextTick(() => {
        const el = document.querySelector(".import-area");
        if (el) el.focus();
      });
    }
    function confirmImport() {
      const el = document.querySelector(".import-area");
      if (!el || !el.value.trim()) {
        importMsg.value = "请先粘贴备份内容";
        importOk.value = false;
        return;
      }
      try {
        const words = importProgress(el.value);
        progress.value = words;
        saveProgress(progress.value);
        importMsg.value = `导入成功：${Object.keys(words).length} 条进度记录`;
        importOk.value = true;
        showImport.value = false;
      } catch (e) {
        importMsg.value = "导入失败：" + e.message;
        importOk.value = false;
      }
    }
    function doReset() {
      if (confirm("确定要重置全部学习进度吗？此操作不可恢复。")) {
        progress.value = {};
        saveProgress(progress.value);
        importMsg.value = "已重置全部进度";
        importOk.value = true;
      }
    }

    // ---- 导航 ----
    function go(v) {
      view.value = v;
      sidebarOpen.value = false;
    }

    // ---- 键盘快捷键 ----
    function onKeydown(e) {
      if (view.value !== "learn" || !currentWord.value) return;
      if (e.code === "Space") {
        e.preventDefault();
        if (!revealed.value) reveal();
      } else if (revealed.value) {
        if (e.code === "Digit1" || e.code === "Numpad1") mark("zhan");
        else if (e.code === "Digit2" || e.code === "Numpad2") mark("shi");
        else if (e.code === "Digit3" || e.code === "Numpad3") mark("hu");
      }
    }

    // ---- 生命周期 ----
    onMounted(async () => {
      await loadLexicon();
      startNewSession();
      window.addEventListener("keydown", onKeydown);
    });
    onBeforeUnmount(() => {
      window.removeEventListener("keydown", onKeydown);
      stopSpeak();
    });

    // 设置变化持久化
    watch(dailyTarget, (v) => localStorage.setItem("ielts-daily", String(v)));
    watch(accent, (v) => localStorage.setItem("ielts-accent", v));

    return {
      view, sidebarOpen, accent, dailyTarget,
      lexicon, lexiconMeta, loaded, progress,
      sessionQueue, sessionIndex, sessionNew, revealed,
      spellInput, spellResult, spellOk,
      searchQuery, activeMarkFilter, detailWord, tokenTip, tipStyle,
      showImport, importMsg, importOk,
      markFilters,
      stats, todayLearned, dueWords, dueCount, currentWord, sessionProgress,
      exampleTokens, detailTokens, filteredWords,
      go, startNewSession, reveal, playWord, checkSpell, mark,
      openWordDetail, openReview, markWordInDetail,
      showTokenTip, hideTokenTip, playToken, lookupToken,
      filterBrowse, setMarkFilter, setAccent,
      doExport, doImport, confirmImport, doReset,
      shortTrans, markLabel, pct,
    };
  },
};
</script>
