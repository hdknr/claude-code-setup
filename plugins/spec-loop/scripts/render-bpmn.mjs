// BPMN（`*.bpmn`）1 枚を、bpmn-js（Camunda Modeler と同じ描画部品）で SVG に書き出す描画口。
//
// usage: node render-bpmn.mjs --deps <依存のディレクトリ> --chrome <Chrome の実行ファイル> <入力.bpmn> <出力.svg>
//
// **`render-diagrams.py` から呼ばれる**（`*.bpmn` の既定の描画口）。印（ソースの指紋）を書き込むのも、
// 書き出しを `X.svg` に置くのも `render-diagrams.py` で、ここは渡された出力のパスに SVG を書くだけである。
// 決まり（どこに置くか・何を守り何を守らないか）は `render-diagrams.py` の docstring と `references/tree.md` の「図」を正とする。
//
// - `<依存のディレクトリ>` は `npm install bpmn-js puppeteer-core` を走らせた場所（`node_modules/` を持つ）。
//   bpmn-js の viewer（`dist/bpmn-viewer.production.min.js`）と CSS をそこから読み、puppeteer-core をそこから読み込む。
// - headless の Chrome でページを開き、viewer に XML を読ませて `saveSVG()` の結果を書く。
// - **読み込みの警告（`importXML` の warnings）が 1 つでもあれば失敗にする**——描けなかった要素を落とした図を書き出さない。
// - 失敗したら標準エラーに理由を書いて 0 以外で終わる（出力のパスには書かない）。
// - Chrome とは pipe でつなぐ——このプロセスが止められて pipe が閉じたら Chrome も終わる。
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { createRequire } from 'node:module';

function fail(message) {
  process.stderr.write(`render-bpmn: ${message}\n`);
  process.exit(1);
}

const argv = process.argv.slice(2);
const options = {};
const positional = [];
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === '--deps' || argv[i] === '--chrome') {
    if (i + 1 >= argv.length) fail(`${argv[i]} の値が無い`);
    options[argv[i].slice(2)] = argv[++i];
  } else {
    positional.push(argv[i]);
  }
}
if (!options.deps || !options.chrome || positional.length !== 2) {
  fail('usage: node render-bpmn.mjs --deps <依存のディレクトリ> --chrome <Chrome> <入力.bpmn> <出力.svg>');
}
const [input, output] = positional;
const dist = join(options.deps, 'node_modules', 'bpmn-js', 'dist');
const viewerPath = join(dist, 'bpmn-viewer.production.min.js');
for (const path of [viewerPath, join(dist, 'assets', 'diagram-js.css'), join(dist, 'assets', 'bpmn-js.css')]) {
  if (!existsSync(path)) fail(`bpmn-js が無い（${path}）`);
}
if (!existsSync(options.chrome)) fail(`Chrome が無い（${options.chrome}）`);

let puppeteer;
try {
  const required = createRequire(join(options.deps, 'package.json'))('puppeteer-core');
  puppeteer = typeof required.launch === 'function' ? required : required.default;
} catch (e) {
  fail(`puppeteer-core を読み込めない（${e.message}）`);
}
if (!puppeteer || typeof puppeteer.launch !== 'function') fail('puppeteer-core に launch が無い');

const viewer = readFileSync(viewerPath, 'utf8');
const css = ['diagram-js.css', 'bpmn-js.css'].map((name) => readFileSync(join(dist, 'assets', name), 'utf8')).join('\n');
const xml = readFileSync(input, 'utf8');

let browser;
let code = 0;
try {
  browser = await puppeteer.launch({ executablePath: options.chrome, headless: true, pipe: true });
  const page = await browser.newPage();
  await page.setViewport({ width: 2400, height: 1600, deviceScaleFactor: 1 });
  await page.setContent(`<html><head><style>${css} body{margin:0;background:#fff} #c{width:2400px;height:1600px}</style></head>`
    + '<body><div id="c"></div></body></html>');
  await page.addScriptTag({ content: viewer });
  const result = await page.evaluate(async (source) => {
    // eslint-disable-next-line no-undef
    const bpmn = new BpmnJS({ container: '#c' });
    try {
      const { warnings } = await bpmn.importXML(source);
      if (warnings.length) return { warnings: warnings.map((w) => w.message) };
      const { svg } = await bpmn.saveSVG();
      return { svg };
    } catch (e) {
      return { error: String(e && e.message ? e.message : e) };
    }
  }, xml);
  if (result.error) {
    process.stderr.write(`render-bpmn: BPMN を読めない（${result.error}）\n`);
    code = 1;
  } else if (result.warnings) {
    process.stderr.write(`render-bpmn: 読み込みに警告がある（${result.warnings.length} 件。書き出さない）:\n  ${result.warnings.join('\n  ')}\n`);
    code = 1;
  } else {
    writeFileSync(output, result.svg);
  }
} catch (e) {
  process.stderr.write(`render-bpmn: 描画できない（${e && e.message ? e.message : e}）\n`);
  code = 1;
} finally {
  if (browser) await browser.close().catch(() => {});
}
process.exit(code);
