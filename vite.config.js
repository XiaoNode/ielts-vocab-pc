import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [
    vue(),
    // 将 JS/CSS 全部内联进单个 index.html，支持 file:// 双击直开
    viteSingleFile(),
  ],
  base: "./",
  build: {
    target: "es2020",
    chunkSizeWarningLimit: 4000,
    // 内联单文件时禁用 CSS 代码分割，避免产出单独 css 文件
    cssCodeSplit: false,
  },
});
