// Renderiza en lote expresiones LaTeX con KaTeX (lado servidor).
// Entrada (stdin): JSON [{id, tex, display}]  Salida (stdout): JSON {id: {html, error}}
const katex = require("katex");
let buf = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (d) => (buf += d));
process.stdin.on("end", () => {
  const items = JSON.parse(buf);
  const out = {};
  const macros = {};
  for (const it of items) {
    try {
      out[it.id] = {
        html: katex.renderToString(it.tex, {
          displayMode: !!it.display,
          throwOnError: true,
          strict: "ignore",
          trust: false,
          output: "html",
          macros,
        }),
        error: null,
      };
    } catch (e) {
      let html = "";
      try {
        html = katex.renderToString(it.tex, { displayMode: !!it.display, throwOnError: false, strict: "ignore", output: "html" });
      } catch (e2) {}
      out[it.id] = { html, error: String(e.message || e) };
    }
  }
  process.stdout.write(JSON.stringify(out));
});
