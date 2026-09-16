import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gate } from './gate.mjs';

const report = status => ({ schemaVersion: 1, rulesVersion: 'fixture-1', generatedAt: '2026-09-16T12:00:00Z', scope: 'Synthetic gate fixture; not a website audit', pageCount: 1, issues: [{ name: 'canonical', url: '/service/', status, evidence: { observed: 'fixture' }, recommendation: status === 'pass' ? '' : 'Inspect canonical output.' }], unmeasured: ['Live website'] });
test('valid passing evidence returns zero', () => assert.equal(gate(report('pass'), () => {}), 0));
test('warning stays visible and is nonblocking', () => { const lines = []; assert.equal(gate(report('warning'), line => lines.push(line)), 0); assert.ok(lines.some(line => line.startsWith('SEO_WARNING'))); });
test('error fails even when an optional summary says passed', () => assert.equal(gate({ ...report('error'), summary: { errors: 0, passed: 100 } }, () => {}), 1));
test('incomplete or unknown contracts fail closed', () => {
  for (const value of [null, {}, { ...report('pass'), issues: [] }, { ...report('pass'), pageCount: 0 }, { ...report('pass'), schemaVersion: 2 }, { ...report('pass'), unmeasured: null }, { ...report('pass'), generatedAt: 'yesterday' }, report('green')]) assert.equal(gate(value, () => {}), 2);
});
test('missing evidence or remediation fails closed', () => {
  for (const field of ['evidence', 'recommendation', 'url']) { const value = report('error'); delete value.issues[0][field]; assert.equal(gate(value, () => {}), 2); }
});
test('finding labels cannot inject terminal lines', () => { const value = report('error'); value.issues[0].name = 'bad\n\u001b[31m'; const lines = []; gate(value, line => lines.push(line)); assert.ok(!lines[0].includes('\n')); assert.ok(!lines[0].includes('\u001b')); });
test('CLI preserves exit codes for valid, error, malformed and missing input', () => {
  const dir = mkdtempSync(join(tmpdir(), 'seo-gate-'));
  const script = fileURLToPath(new URL('./gate.mjs', import.meta.url));
  try {
    for (const [name, data, expected] of [['pass', JSON.stringify(report('pass')), 0], ['error', JSON.stringify(report('error')), 1], ['malformed', '{', 2], ['contract', '{}', 2]]) {
      const path = join(dir, name + '.json'); writeFileSync(path, data);
      assert.equal(spawnSync(process.execPath, [script, path]).status, expected);
    }
    assert.equal(spawnSync(process.execPath, [script]).status, 2);
    assert.equal(spawnSync(process.execPath, [script, join(dir, 'missing.json')]).status, 2);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
