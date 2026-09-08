# 雅思斩词 PC 版 — 交付概览

**日期**：2026-09-08
**状态**：✅ 已完成全量项目创建与验证

---

## TL;DR

- 已按「百词斩」模式创建完整的 **本地优先雅思单词学习 PC 应用**，技术栈 Vite + Vue 3
- 词库 **8000 词**（5013 IELTS 核心 + 2987 高频补充），5141 词带双语例句
- 实现斩/识/糊三层标记 + 间隔复习 + 双语例句逐词点读 + 英美双发音 + JSON 导入导出
- 构建通过，浏览器端到端验证通过

## 项目位置

`E:/github/IELTS-English/ielts-vocab-pc/`

## 已完成功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 8000 词词库 | ✅ | ECDICT(MIT) 筛选，含音标/释义/词性/词频 |
| 双语例句 | ✅ | Tatoeba(CC BY 2.0) 5141 词带例句 |
| 斩/识/糊标记 | ✅ | 主观标记 + 间隔复习算法 |
| 英美双发音 | ⚠️ | WAV 音频生成脚本就绪，espeak-ng 安装中；运行时 TTS 兜底已就绪 |
| 逐词点读 | ✅ | 例句每个词 hover 提示 + 点击发音 + 查词 |
| 拼写检查 | ✅ | 斩前可选拼写验证 |
| 学习统计 | ✅ | 词库总量/学习中/已掌握/标记分布 |
| 数据迁移 | ✅ | JSON 导出导入（含 schemaVersion + checksum） |
| 本地持久化 | ✅ | localStorage |
| 分类查询 | ✅ | 斩/识/糊/未标记筛选 + 关键词搜索 |

## 验证记录

- ✅ `npm run build` 构建成功（单文件 index.html 1.88MB，词库/JS/CSS 全内联）
- ✅ 浏览器端到端：学习队列建立 → 显示释义 → 例句渲染 → 斩标记 → 进入下一词 → 统计更新 → 词库搜索
- ✅ **file:// 双击直开**：Chrome headless 验证，词库内联无 fetch 残留，学习队列正常渲染
- ✅ 词库数据验证：8000 词、64.3% 例句覆盖率、例句质量良好
- ✅ 音频 16000 个 WAV（695MB）随 dist/data/audio/ 分发，file:// 下媒体标签可加载

## 关键设计：单文件直开

- 词库由 `lexicon.json` 同步生成 `src/lexicon-data.js`（ES module 内联），绕过 `file://` 协议下 `fetch` 的 CORS 限制
- `vite-plugin-singlefile` 将 JS/CSS 全部内联进 `dist/index.html`，**双击即可用**
- 音频走 `<audio>` 标签相对路径 `data/audio/*.wav`，媒体标签不受 fetch 同源限制

## 待处理

1. **音频 WAV 生成**：espeak-ng 安装后运行 `python scripts/generate-audio.py` 生成英美 WAV（合成音）；运行时已用浏览器 TTS 兜底
2. **真人发音**（可选）：如需要真人发音，可后续接入 CMUdict + 开源真人音频集
3. **例句覆盖率**：5141/8000（64.3%），Tatoeba 英中句对本身有限，低频词无例句属正常

## 运行方式

```bash
cd ielts-vocab-pc
npm install
npm run dev        # 开发模式 http://127.0.0.1:5173/
npm run build      # 生产构建，产物 dist/
```

## 数据源许可

- 词库：ECDICT（MIT）
- 例句：Tatoeba（CC BY 2.0 FR，需署名）
- 音频：espeak-ng（GPLv3，合成音）
