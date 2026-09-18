#!/usr/bin/env node
/**
 * Check store/metadata.md against App Store Connect's field limits.
 *
 *     node ios/tools/check-metadata.mjs
 *
 * The limits are Apple's, and the form enforces them by truncating or
 * refusing at the moment of paste -- which is the worst moment to be
 * rewriting a description. Counting them here means the text in the repo is
 * known to fit before anybody opens the browser.
 *
 * Each field is the indented block under its heading. The heading carries the
 * limit in parentheses, so a heading and its rule cannot drift apart: there is
 * nothing to keep in step, because the limit is read from the same line the
 * reader sees.
 *
 * Apple counts characters, not bytes, and a newline counts as one. Keywords
 * are a special case: the 100 characters include the commas, and a space
 * after a comma costs one of them for nothing, so they are checked for that
 * too.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const IOS = dirname(dirname(fileURLToPath(import.meta.url)));
const FILE = join(IOS, 'store', 'metadata.md');

const text = readFileSync(FILE, 'utf8');
const lines = text.split(/\r?\n/);

/** Headings of the form `## Name (30)` -- the ones with a counted limit. */
const HEADING = /^##\s+(.+?)\s+\((\d+)\)\s*$/;

const fields = [];
for (let i = 0; i < lines.length; i += 1) {
  const m = HEADING.exec(lines[i]);
  if (!m) continue;

  // The field is the first indented block after the heading; prose between
  // the two is commentary for whoever is pasting.
  const body = [];
  let started = false;
  for (let j = i + 1; j < lines.length && !HEADING.test(lines[j]); j += 1) {
    const indented = /^ {4}(.*)$/.exec(lines[j]);
    if (indented) {
      started = true;
      body.push(indented[1]);
    } else if (started && lines[j].trim() === '') {
      // A blank line inside the block is part of the text; one after it ends
      // the block only if nothing indented follows.
      const more = lines.slice(j + 1).findIndex((l) => l.trim() !== '');
      if (more === -1 || !/^ {4}/.test(lines[j + 1 + more])) break;
      body.push('');
    } else if (started) {
      break;
    }
  }

  fields.push({ name: m[1], limit: Number(m[2]), value: body.join('\n').trim() });
}

if (fields.length === 0) {
  console.error(`no counted fields found in ${FILE}; has the heading format changed?`);
  process.exit(1);
}

let failed = 0;
for (const f of fields) {
  const n = [...f.value].length;
  const over = n > f.limit;
  if (over) failed += 1;
  console.log(
    `${over ? 'OVER ' : '  ok '} ${f.name.padEnd(18)} ${String(n).padStart(4)} / ${f.limit}`
  );
  if (f.name.toLowerCase().startsWith('keywords')) {
    if (/,\s/.test(f.value)) {
      console.log('       keywords: a space after a comma costs a character and buys nothing');
      failed += 1;
    }
    if (/\b2048\b/.test(f.value)) {
      console.log('       keywords: "2048" is another app\'s name -- see the note in metadata.md');
      failed += 1;
    }
  }
}

if (failed) {
  console.error(`\n${failed} problem(s) in ${FILE}`);
  process.exit(1);
}
console.log(`\n${fields.length} field(s) within their limits.`);
