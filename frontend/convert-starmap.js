const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(path.join("public", "student-steps-starmap.html"), "utf8");

const clean = html.replace(/\s+data-page-node-id="[^"]*"/g, "");

const styleMatch = clean.match(/<style>([\s\S]*?)<\/style>/);
const scriptMatch = clean.match(/<script>([\s\S]*?)<\/script>/);
const bodyMatch = clean.match(/<body>([\s\S]*)<\/body>/);

if (!styleMatch || !scriptMatch || !bodyMatch) {
  console.error("parse failed");
  process.exit(1);
}

let style = styleMatch[1];
style = style.replace(/:root\s*\{/g, ".app {");
style = style.replace(/\banimation: sunIn\b/g, "animation: sunInStudent");
style = style.replace(/\banimation: fadeIn\b/g, "animation: fadeInStudent");
style = style.replace(/@keyframes sunIn\b/g, "@keyframes sunInStudent");
style = style.replace(/@keyframes fadeIn\b/g, "@keyframes fadeInStudent");

let script = scriptMatch[1].trim();
script = script.replace(/document\.querySelector\('\.app'\)/g, "document.getElementById('studentStepsApp')");

let body = bodyMatch[1].trim();
body = body.replace(/<div class="app"/g, '<div id="studentStepsApp" class="app"');

const vue = `<template>
${body}
</template>

<script setup>
import { onMounted } from "vue"
onMounted(() => {
${script.split("\n").map((l) => "  " + l).join("\n")}
})
<\/script>

<style scoped>
${style}
</style>
`;

fs.writeFileSync(path.join("src", "views", "StudentStepsStarmap.vue"), vue);
console.log("Generated src/views/StudentStepsStarmap.vue, bytes:", vue.length);
