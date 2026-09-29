/* Pull the page's main script out of the built HTML. */
const fs = require("fs");
const html = fs.readFileSync(process.argv[2] || "../dist/ki-journal-list.html", "utf8");
const i = html.lastIndexOf('<script>');
const j = html.indexOf('</script>', i);
fs.writeFileSync(process.argv[3] || "page.js", html.slice(i + 8, j));
console.log("extracted", (j - i) / 1024 | 0, "kB");
