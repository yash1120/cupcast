// Fetch Magic UI components from the public shadcn-style registry into
// src/components/magicui/, collecting any Tailwind v4 CSS additions.
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const COMPONENTS = ["magic-card", "number-ticker", "animated-gradient-text",
  "border-beam", "shimmer-button", "marquee"];
const outDir = path.resolve(import.meta.dirname, "../src/components/magicui");
await mkdir(outDir, { recursive: true });

let cssParts = [];
for (const name of COMPONENTS) {
  const res = await fetch(`https://magicui.design/r/${name}.json`);
  if (!res.ok) { console.error(`FAILED ${name}: ${res.status}`); continue; }
  const item = await res.json();
  for (const f of item.files ?? []) {
    const base = path.basename(f.path);
    await writeFile(path.join(outDir, base), f.content, "utf8");
    console.log(`wrote magicui/${base}`);
  }
  if (item.css) cssParts.push(`/* ${name} */\n${JSON.stringify(item.css, null, 2)}`);
  if (item.cssVars) cssParts.push(`/* ${name} vars */\n${JSON.stringify(item.cssVars, null, 2)}`);
  if (item.dependencies?.length) console.log(`  deps: ${item.dependencies.join(", ")}`);
}
if (cssParts.length) {
  await writeFile(path.resolve(import.meta.dirname, "../magicui-css-notes.txt"),
    cssParts.join("\n\n"), "utf8");
  console.log("css notes -> magicui-css-notes.txt");
}
