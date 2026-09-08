// 发音引擎：优先本地 WAV 音频（public/data/audio/），兜底浏览器 SpeechSynthesis
// 支持英式 (gb/en-GB) 与美式 (us/en-US) 两种口音

const AUDIO_BASE = "data/audio/";

let cachedVoices = null;

function loadVoices() {
  return new Promise((resolve) => {
    if (!("speechSynthesis" in window)) {
      cachedVoices = [];
      resolve([]);
      return;
    }
    const voices = window.speechSynthesis.getVoices();
    if (voices && voices.length) {
      cachedVoices = voices;
      resolve(voices);
      return;
    }
    window.speechSynthesis.onvoiceschanged = () => {
      cachedVoices = window.speechSynthesis.getVoices();
      resolve(cachedVoices);
    };
    // 兜底：1 秒后仍未加载则返回空
    setTimeout(() => {
      if (!cachedVoices) cachedVoices = [];
      resolve(cachedVoices);
    }, 1000);
  });
}

function pickVoice(accent) {
  const voices = cachedVoices || [];
  if (!voices.length) return null;
  const lang = accent === "gb" ? "en-GB" : "en-US";
  const prefix = accent === "gb" ? "en-gb" : "en-us";
  // 优先精确语言匹配
  let v = voices.find((x) => x.lang && x.lang.toLowerCase().replace("_", "-") === lang);
  if (!v) {
    v = voices.find((x) => x.lang && x.lang.toLowerCase().startsWith(prefix));
  }
  if (!v) v = voices.find((x) => x.lang && x.lang.toLowerCase().startsWith("en"));
  return v || null;
}

/**
 * 朗读单词或句子
 * @param {string} text 要朗读的文本
 * @param {string} accent 'us' | 'gb'
 * @param {string} word  可选：单词本身（用于匹配本地 WAV 文件）
 * @returns {Promise<void>}
 */
export async function speak(text, accent = "us", word = null) {
  const cleanWord = (word || text).toLowerCase().replace(/[^a-z']/g, "");
  const audioUrl = `${AUDIO_BASE}${cleanWord}_${accent}.wav`;

  // 1) 尝试本地音频
  if (cleanWord && (word || text.split(/\s+/).length === 1)) {
    const ok = await tryPlayAudio(audioUrl);
    if (ok) return;
  }

  // 2) 兜底 SpeechSynthesis
  if ("speechSynthesis" in window) {
    await loadVoices();
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    const voice = pickVoice(accent);
    if (voice) u.voice = voice;
    u.lang = accent === "gb" ? "en-GB" : "en-US";
    u.rate = 0.9;
    window.speechSynthesis.speak(u);
  }
}

function tryPlayAudio(url) {
  return new Promise((resolve) => {
    try {
      const audio = new Audio(url);
      let settled = false;
      const finish = (ok) => {
        if (!settled) {
          settled = true;
          resolve(ok);
        }
      };
      audio.oncanplaythrough = () => {
        audio.play().then(() => finish(true)).catch(() => finish(false));
      };
      audio.onerror = () => finish(false);
      // 超时：若无法快速加载则放弃本地音频
      setTimeout(() => finish(false), 1500);
      audio.preload = "auto";
    } catch (e) {
      resolve(false);
    }
  });
}

/** 停止当前朗读 */
export function stopSpeak() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

export default { speak, stopSpeak };
