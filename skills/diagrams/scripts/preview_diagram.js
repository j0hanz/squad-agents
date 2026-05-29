const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');

const filePath = process.argv[2];
if (!filePath) {
    console.error('Usage: node preview_diagram.js <file.mmd>');
    process.exit(1);
}

const content = fs.readFileSync(filePath, 'utf-8');
const data = Buffer.from(content, 'utf8');
const compressed = zlib.deflateSync(data);
const encoded = compressed.toString('base64').replace(/\+/g, '-').replace(/\//g, '_');

const url = `https://kroki.io/mermaid/svg/${encoded}`;
const htmlContent = `<html><body style="margin:0;display:flex;justify-content:center;align-items:center;height:100vh;background:#fff;"><img src="${url}" alt="Diagram Preview"/></body></html>`;

const previewPath = path.join(require('os').tmpdir(), 'mermaid_preview.html');
fs.writeFileSync(previewPath, htmlContent);

console.log(`Preview URL: ${url}`);
console.log(`Local File : ${previewPath}`);