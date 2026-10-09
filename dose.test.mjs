import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateDose, summarize, parseCsv, exportCsv } from './dose.mjs';

test('CTDIvol times length gives DLP without an automatic effective-dose claim', () => {
  const d = calculateDose({ ctdi: 12, length: 35 });
  assert.equal(d.dlpMgyCm, 420);
  assert.equal(d.effectiveMsv, null);
});

test('reported DLP overrides calculated DLP and explicit coefficient is applied', () => {
  const d = calculateDose({ ctdi: 12, length: 35, dlp: 450, k: 0.014 });
  assert.equal(d.calculatedDlpMgyCm, 420);
  assert.equal(d.dlpMgyCm, 450);
  assert.ok(Math.abs(d.effectiveMsv - 6.3) < 1e-10);
});

test('invalid values and missing DLP are rejected', () => {
  for (const row of [{}, { ctdi: 10 }, { ctdi: -1, length: 30 },
    { ctdi: 10, length: 0 }, { dlp: 'NaN' }, { dlp: Infinity },
    { dlp: 300, k: -1 }]) {
    assert.throws(() => calculateDose(row));
  }
});

test('reported zero DLP is not treated as absent', () => {
  assert.equal(calculateDose({dlp: '0'}).dlpMgyCm, 0);
});

test('sum reports partial effective estimate coverage', () => {
  const doses = [{ dose: calculateDose({dlp: 300, k: .014}) },
                 { dose: calculateDose({dlp: 200}) }];
  assert.deepEqual(summarize(doses), { count: 2, dlpMgyCm: 500,
    effectiveMsv: 4.2, effectiveKnownCount: 1 });
});

test('CSV parser supports BOM, CRLF, quoted newlines and doubled quotes', () => {
  const r = parseCsv('\uFEFFprotocol,dlp_mgy_cm\r\n"Chest, contrast",300\r\n"Head ""plain""\nseries",200\r\n');
  assert.equal(r[0].protocol, 'Chest, contrast');
  assert.equal(r[1].protocol, 'Head "plain"\nseries');
  assert.equal(r.length, 2);
});

test('CSV parser rejects bad rows and duplicate headers', () => {
  assert.throws(() => parseCsv('a,a\nx,y'));
  assert.throws(() => parseCsv('a,b\nx'));
  assert.throws(() => parseCsv('a\n"missing'));
});

test('CSV export neutralizes spreadsheet formula text', () => {
  const csv = exportCsv([{ protocol: '=HYPERLINK("bad")', dose: calculateDose({dlp: 10}) }]);
  assert.ok(csv.includes('"\'=HYPERLINK(""bad"")"'));
  assert.ok(csv.includes('"10"'));
});
