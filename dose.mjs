/**
 * CT scanner-output metrics. Not an individual patient dose or risk estimator.
 * AAPM Report 96: DLP = CTDIvol x irradiated length; E ~= DLP x k.
 */
export function numberOrNull(raw, label, { positive = false } = {}) {
  if (raw === null || raw === undefined || String(raw).trim() === '') return null;
  const n = Number(raw);
  if (!Number.isFinite(n) || n < 0 || (positive && n === 0)) {
    throw new Error(label + ' must be a finite ' + (positive ? 'positive' : 'non-negative') + ' number.');
  }
  return n;
}

export function calculateDose({ ctdi, length, dlp, k } = {}) {
  const c = numberOrNull(ctdi, 'CTDIvol');
  const l = numberOrNull(length, 'Scan length', { positive: true });
  const reported = numberOrNull(dlp, 'Reported DLP');
  const coefficient = numberOrNull(k, 'Conversion coefficient');
  if (reported === null && (c === null || l === null)) {
    throw new Error('Provide reported DLP, or both CTDIvol and scan length.');
  }
  const calculatedDlp = c !== null && l !== null ? c * l : null;
  const effectiveDlp = reported === null ? calculatedDlp : reported;
  if (!Number.isFinite(effectiveDlp)) throw new Error('Calculated DLP exceeds numeric range.');
  const effectiveMsv = coefficient === null ? null : effectiveDlp * coefficient;
  if (effectiveMsv !== null && !Number.isFinite(effectiveMsv)) {
    throw new Error('Effective dose estimate exceeds numeric range.');
  }
  return {
    ctdiMgy: c, lengthCm: l, dlpMgyCm: effectiveDlp,
    reportedDlp: reported !== null, calculatedDlpMgyCm: calculatedDlp,
    coefficient, effectiveMsv
  };
}

export function summarize(rows) {
  return rows.reduce((totals, item) => {
    totals.count++;
    totals.dlpMgyCm += item.dose.dlpMgyCm;
    if (item.dose.effectiveMsv !== null) {
      totals.effectiveKnownCount++;
      totals.effectiveMsv += item.dose.effectiveMsv;
    }
    return totals;
  }, { count: 0, dlpMgyCm: 0, effectiveMsv: 0, effectiveKnownCount: 0 });
}

// RFC 4180-style CSV with quoted commas, newlines, and escaped double quotes.
export function parseCsv(input) {
  if (typeof input !== 'string') throw new Error('CSV input must be text.');
  const text = input.replace(/^\uFEFF/, '');
  const rows = [];
  let row = [], field = '', quoted = false, afterQuote = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else { quoted = false; afterQuote = true; }
      } else field += ch;
    } else if (ch === '"' && !field && !afterQuote) {
      quoted = true;
    } else if (ch === ',') {
      row.push(field); field = ''; afterQuote = false;
    } else if (ch === '\r' || ch === '\n') {
      if (ch === '\r' && text[i + 1] === '\n') i++;
      row.push(field);
      if (row.some(cell => cell !== '')) rows.push(row);
      row = []; field = ''; afterQuote = false;
    } else {
      if (afterQuote || ch === '"') throw new Error('Malformed CSV: unexpected characters after closing quote.');
      field += ch;
    }
  }
  if (quoted) throw new Error('Malformed CSV: unclosed quoted field.');
  if (field !== '' || row.length) {
    row.push(field);
    if (row.some(cell => cell !== '')) rows.push(row);
  }
  if (!rows.length) throw new Error('CSV is empty.');
  const headers = rows.shift().map(x => x.trim().toLowerCase());
  if (new Set(headers).size !== headers.length) throw new Error('Duplicate CSV headers.');
  if (rows.length > 2000) throw new Error('CSV exceeds 2,000 examinations.');
  return rows.map((values, i) => {
    if (values.length !== headers.length) throw new Error('CSV row ' + (i + 2) + ' has a different field count.');
    return Object.fromEntries(headers.map((h, j) => [h, values[j]]));
  });
}

export function escapeCsvCell(value) {
  let str = value == null ? '' : String(value);
  if (/^\s*[=+@-]/.test(str)) str = "'" + str; // Prevent spreadsheet formula execution on export.
  return '"' + str.replace(/"/g, '""') + '"';
}

export function exportCsv(rows) {
  const columns = ['protocol', 'ctdi_vol_mgy', 'scan_length_cm', 'dlp_mgy_cm', 'k_msv_per_mgy_cm', 'effective_msv'];
  const lines = [columns.join(',')];
  for (const { protocol, dose } of rows) {
    lines.push([
      protocol, dose.ctdiMgy, dose.lengthCm, dose.dlpMgyCm,
      dose.coefficient, dose.effectiveMsv
    ].map(escapeCsvCell).join(','));
  }
  return '\uFEFF' + lines.join('\r\n') + '\r\n';
}
