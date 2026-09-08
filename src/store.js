// 学习进度持久化：localStorage 主存 + IndexedDB 可选（大数据）
// 状态模型：
//   每个词：{ word, status: 'new'|'learning'|'known'|'mastered', 主观标记:'zhan'|'shi'|'hu',
//            dueAt: 下次复习时间戳, streak: 连续答对次数, verified: 客观掌握,
//            lastResultDay: 上次答对日期 }

const STORAGE_KEY = "ielts-vocab-progress-v1";

const DAY_MS = 24 * 3600 * 1000;

// 间隔复习：糊 10min / 识 1day / 斩 3day(未验证) 7day(已验证)
export const INTERVALS = {
  fuzzy: 10 * 60 * 1000, // 糊：10 分钟
  know: 1 * DAY_MS, // 识：1 天
  zhanUnverified: 3 * DAY_MS, // 斩（未验证）：3 天
  zhanVerified: 7 * DAY_MS, // 斩（已验证）：7 天
};

export function todayStr(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function loadProgress() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const data = JSON.parse(raw);
    return data.words || {};
  } catch (e) {
    console.warn("loadProgress failed", e);
    return {};
  }
}

export function saveProgress(words) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ words, savedAt: Date.now() }));
  } catch (e) {
    console.error("saveProgress failed", e);
  }
}

/**
 * 记录一次作答结果，返回更新后的词条状态
 * @param {object} rec 现有记录（可为空）
 * @param {string} mark 'zhan'|'shi'|'hu'  主观标记（斩/识/糊）
 * @param {boolean} correct 客观是否答对（主动回忆/拼写正确）
 */
export function applyResult(rec, mark, correct) {
  const now = Date.now();
  const day = todayStr();
  const r = rec || { status: "new", mark: null, streak: 0, verified: false, dueAt: 0, lastResultDay: null, lastSeen: 0 };

  r.lastSeen = now;

  if (mark === "hu" || (mark === "shi" && !correct)) {
    // 糊（或识但答错）：10 分钟后复习
    r.dueAt = now + INTERVALS.fuzzy;
    r.streak = 0;
    r.verified = false;
    r.status = "learning";
  } else if (mark === "shi") {
    // 识（答对）：1 天后
    r.dueAt = now + INTERVALS.know;
    r.streak = Math.min((r.streak || 0) + 1, 99);
    r.status = "learning";
    r.lastResultDay = day;
  } else if (mark === "zhan") {
    // 斩：答对且主观标记已熟记
    const crossDay = r.lastResultDay && r.lastResultDay !== day;
    r.streak = Math.min((r.streak || 0) + 1, 99);
    // 客观掌握：跨天 + 连续 >=2 次斩
    r.verified = r.verified || (crossDay && r.streak >= 2);
    r.dueAt = now + (r.verified ? INTERVALS.zhanVerified : INTERVALS.zhanUnverified);
    r.status = r.verified ? "mastered" : "learning";
    r.lastResultDay = day;
  }

  r.mark = mark;
  return r;
}

/** 计算学习统计 */
export function computeStats(words) {
  const total = Object.keys(words).length;
  let newCount = 0, learning = 0, mastered = 0, verified = 0;
  const markCount = { zhan: 0, shi: 0, hu: 0, none: 0 };
  for (const w of Object.values(words)) {
    if (w.status === "new") newCount++;
    else if (w.status === "mastered") mastered++;
    else learning++;
    if (w.verified) verified++;
    if (w.mark === "zhan") markCount.zhan++;
    else if (w.mark === "shi") markCount.shi++;
    else if (w.mark === "hu") markCount.hu++;
    else markCount.none++;
  }
  return { total, newCount, learning, mastered, verified, markCount };
}

/**
 * 导出进度为 JSON 字符串（含 schemaVersion + checksum）
 * @param {object} lexicon 词库（用于校验完整性）
 */
export function exportProgress(words, lexiconMeta) {
  const payload = {
    schemaVersion: 1,
    app: "ielts-vocab-pc",
    exportedAt: new Date().toISOString(),
    lexicon: lexiconMeta || null,
    words,
  };
  const json = JSON.stringify(payload, null, 2);
  // 简单 checksum（字符和）
  let sum = 0;
  for (let i = 0; i < json.length; i++) sum = (sum + json.charCodeAt(i)) % 65536;
  payload.checksum = sum.toString(16).padStart(4, "0");
  return JSON.stringify(payload, null, 2);
}

/** 导入进度，返回解析后的 words 对象 */
export function importProgress(jsonStr) {
  const data = JSON.parse(jsonStr);
  if (!data || typeof data.words !== "object") {
    throw new Error("无效的备份文件：缺少 words 字段");
  }
  if (!data.schemaVersion) {
    throw new Error("无效的备份文件：缺少 schemaVersion");
  }
  return data.words;
}

export default { loadProgress, saveProgress, applyResult, computeStats, exportProgress, importProgress, INTERVALS, todayStr };
