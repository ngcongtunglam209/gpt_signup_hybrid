/* Parse upi.js bằng Node để verify JS syntax (regex literals + IIFE).
 * Dùng `new Function(src)` — strict, không thực thi.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const targets = [
  path.join(ROOT, 'web', 'static', 'upi.js'),
];

let failed = 0;
for (const p of targets) {
  const rel = path.relative(ROOT, p);
  let src;
  try {
    src = fs.readFileSync(p, 'utf8');
  } catch (err) {
    console.log(`[FAIL] ${rel} :: read error: ${err.message}`);
    failed += 1;
    continue;
  }
  try {
    // Wrap để nuốt các identifier global của browser khi parse-only.
    new Function(src);
    console.log(`[PASS] ${rel} :: parse ok (${src.split('\n').length} lines)`);
  } catch (err) {
    console.log(`[FAIL] ${rel} :: ${err.name}: ${err.message}`);
    failed += 1;
  }
}

console.log(`\nDone. ${failed} failure(s).`);
process.exit(failed ? 1 : 0);
