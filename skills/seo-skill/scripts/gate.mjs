#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const nonempty = value => typeof value === 'string' && value.trim().length > 0;
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const evidence = value => nonempty(value) || (Array.isArray(value) && value.length > 0) || (object(value) && Object.keys(value).length > 0);

export function validateReport(report) {
  if (!object(report)) return 'report must be an object';
  if (report.schemaVersion !== 1) return 'unsupported schemaVersion';
  for (const key of ['rulesVersion', 'scope']) if (!nonempty(report[key])) return `missing ${key}`;
  if (typeof report.generatedAt !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(report.generatedAt) || !Number.isFinite(Date.parse(report.generatedAt))) return 'invalid generatedAt timestamp';
  if (!Number.isInteger(report.pageCount) || report.pageCount < 1) return 'pageCount must identify at least one inspected page';
  if (!Array.isArray(report.issues) || !report.issues.length) return 'missing or empty issues';
  if (!Array.isArray(report.unmeasured) || !report.unmeasured.every(nonempty)) return 'invalid unmeasured array';
  for (const [index, issue] of report.issues.entries()) {
    if (!object(issue)) return `issues[${index}] must be an object`;
    if (!nonempty(issue.name) || !nonempty(issue.url)) return `issues[${index}] needs name and url`;
    if (!['pass', 'warning', 'error'].includes(issue.status)) return `issues[${index}] has invalid status`;
    if (!evidence(issue.evidence)) return `issues[${index}] needs evidence`;
    if (typeof issue.recommendation !== 'string' || (issue.status !== 'pass' && !nonempty(issue.recommendation))) return `issues[${index}] needs recommendation`;
  }
  return null;
}

// Escape line breaks and terminal controls in untrusted finding labels.
const label = value => JSON.stringify(value);
export function gate(report, write = line => process.stderr.write(line + '\n')) {
  const invalid = validateReport(report);
  if (invalid) { write(`SEO_CONTRACT ${invalid}`); return 2; }
  let errors = 0;
  let warnings = 0;
  for (const issue of report.issues) {
    if (issue.status === 'error') { errors++; write(`SEO_ERROR ${label(issue.name)} ${label(issue.url)}`); }
    if (issue.status === 'warning') { warnings++; write(`SEO_WARNING ${label(issue.name)} ${label(issue.url)}`); }
  }
  write(`SEO_GATE pages=${report.pageCount} checks=${report.issues.length} errors=${errors} warnings=${warnings}`);
  return errors ? 1 : 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (process.argv.length !== 3) {
    process.stderr.write('usage: node gate.mjs <report.json>\n');
    process.exitCode = 2;
  } else {
    try { process.exitCode = gate(JSON.parse(readFileSync(process.argv[2], 'utf8'))); }
    catch { process.stderr.write('SEO_CONTRACT unreadable file or invalid JSON\n'); process.exitCode = 2; }
  }
}
