# IELTS Vocab PC — 本地优先雅思斩词应用

一款完全本地运行的 PC 版雅思单词学习应用，借鉴「百词斩」学习模式，支持斩/识/糊三层标记、双语例句逐词点读、英美双音标发音、学习进度导入导出。

## 特性

- **8000+ 雅思词库**：基于 ECDICT（MIT）筛选，含 5013 个 IELTS 标签核心词 + 高频补充词
- **双语例句逐词点读**：例句来自 Tatoeba（CC BY 2.0 FR），每个英文词 hover 提示、点击发音
- **斩/识/糊三层标记**：主观标记 + 间隔复习（糊 10 分钟 / 识 1 天 / 斩 3-7 天）
- **英美双发音**：本地 WAV 音频优先，缺失回退系统 TTS
- **本地优先**：localStorage 持久化，JSON 一键导入导出，跨电脑无缝迁移
- **无需账号**：完全离线可用，数据不出本机

## 快速开始

```bash
# 1. 安装依赖
npm install

# 2. 生成词库（已生成可跳过）
python scripts/generate-lexicon.py 8000

# 3. 开发模式
npm run dev
# 打开 http://127.0.0.1:5173/

# 4. 生产构建（单文件 + 音频目录）
npm run build
# 产物：
#   dist/index.html        —— 词库/JS/CSS 已全部内联的单文件，双击即可用
#   dist/data/audio/*.wav —— 16000 个英美发音音频（需与 index.html 同目录保留）
# 部署方式：把 dist/ 整个目录拷走即可，无需服务器，直接双击 index.html 开始学习
```

## 目录结构

```
ielts-vocab-pc/
├── index.html
├── package.json
├── vite.config.js
├── src/
│   ├── main.js          # 入口
│   ├── App.vue          # 主组件（学习/复习/浏览/统计/设置）
│   ├── style.css        # 样式
│   ├── audio.js         # 发音引擎（WAV + TTS 兜底）
│   ├── store.js         # 进度持久化 + 间隔复习算法
│   └── lexicon-data.js  # 内联词库（自动生成，供 file:// 直开）
├── scripts/
│   ├── generate-lexicon.py   # 词库生成（ECDICT 筛选 + Tatoeba 例句）
│   ├── generate-audio.py     # 音频生成（espeak-ng）
│   └── download/             # 原始数据（ECDICT + Tatoeba）
└── public/
    └── data/
        ├── lexicon.json      # 生成的 8000 词词库
        └── audio/            # 16000 个英美发音 WAV
```

## 部署到 GitHub Pages

已内置 `.github/workflows/deploy.yml`，推送 `main`/`master` 分支即自动构建并部署。

**首次配置（仅一次）**：

1. 在 GitHub 仓库 **Settings → Pages**，把 Source 改为 **GitHub Actions**（不是 Branch）
2. 推送代码到 GitHub：
   ```bash
   git init
   git add .
   git commit -m "init ielts-vocab-pc"
   git branch -M main
   git remote add origin <你的仓库地址>
   git push -u origin main
   ```
3. Actions 自动跑完 `npm ci` + `build` + `deploy`，站点地址为 `https://<用户名>.github.io/<仓库名>/`

**注意**：
- 离线音频（`public/data/audio/`，697MB）已随源码入库，Pages 上发音完整可用
- 仓库体积约 700MB，首次 push / clone 较慢属正常

## 数据源与许可

| 数据 | 来源 | 许可 | 用途 |
|------|------|------|------|
| 词库 | [ECDICT](https://github.com/skywind3000/ECDICT) | MIT | 单词/音标/释义/词频 |
| 例句 | [Tatoeba](https://tatoeba.org) | CC BY 2.0 FR | 双语例句（需署名） |
| 音频 | espeak-ng 生成 | GPLv3 | 英/美发音（合成音） |

## 学习算法

- **糊**（想不起来）：10 分钟后复习
- **识**（认识但拼写不流畅）：1 天后复习
- **斩**（完全熟记）：3 天后复习；跨天连续 2 次斩 → 已验证，7 天后复习

## 快捷键

- `空格`：显示释义
- `1` / `2` / `3`：斩 / 识 / 糊（释义显示后）
