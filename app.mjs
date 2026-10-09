import { calculateDose, summarize, parseCsv, exportCsv } from './dose.mjs';

const form = document.querySelector('#dose-form');
const body = document.querySelector('#exam-rows');
const status = document.querySelector('#status');
const rows = [];
const $ = id => document.getElementById(id);

function fmt(n, digits = 2) {
  return n == null ? '—' : n.toLocaleString(undefined, { maximumFractionDigits: digits });
}
function report(message, error = false) {
  status.textContent = message;
  status.classList.toggle('error', error);
}
function createCell(row, value) {
  const td = document.createElement('td');
  td.textContent = value;
  row.append(td);
  return td;
}
function render() {
  body.replaceChildren();
  rows.forEach((item, index) => {
    const tr = document.createElement('tr');
    createCell(tr, item.protocol);
    createCell(tr, fmt(item.dose.ctdiMgy));
    createCell(tr, fmt(item.dose.lengthCm));
    createCell(tr, fmt(item.dose.dlpMgyCm));
    createCell(tr, item.dose.effectiveMsv === null ? 'Not estimated' : fmt(item.dose.effectiveMsv, 3));
    const td = document.createElement('td');
    const remove = document.createElement('button');
    remove.className = 'remove';
    remove.type = 'button';
    remove.textContent = 'Remove';
    remove.setAttribute('aria-label', 'Remove ' + item.protocol);
    remove.addEventListener('click', () => {
      rows.splice(index, 1);
      render();
      report('Examination removed.');
    });
    td.append(remove);
    tr.append(td);
    body.append(tr);
  });
  const totals = summarize(rows);
  $('count').textContent = String(totals.count);
  $('total-dlp').textContent = fmt(totals.dlpMgyCm);
  $('total-effective').textContent = totals.effectiveKnownCount
    ? fmt(totals.effectiveMsv, 3) : '—';
  $('coverage').textContent = totals.count
    ? totals.effectiveKnownCount + ' of ' + totals.count + ' examinations have an effective-dose estimate'
    : 'No examinations entered';
  $('empty').hidden = rows.length !== 0;
  $('download').disabled = rows.length === 0;
  $('clear').disabled = rows.length === 0;
}

form.addEventListener('submit', event => {
  event.preventDefault();
  try {
    const protocol = $('protocol').value.trim().slice(0, 80) || 'Untitled examination';
    const dose = calculateDose({
      ctdi: $('ctdi').value, length: $('length').value,
      dlp: $('dlp').value, k: $('k').value
    });
    if (rows.length >= 2000) throw new Error('Maximum of 2,000 examinations reached.');
    rows.push({ protocol, dose });
    render();
    report('Examination added. No information was uploaded or stored.');
    form.reset();
    $('protocol').focus();
  } catch (err) {
    report(err.message, true);
  }
});
$('example').addEventListener('click', () => {
  $('protocol').value = 'Example adult chest';
  $('ctdi').value = '10';
  $('length').value = '30';
  $('dlp').value = '';
  $('k').value = '0.014';
  report('Illustrative values loaded; select Add examination to calculate.');
});
$('clear').addEventListener('click', () => {
  if (!window.confirm('Clear all examinations in this browser tab?')) return;
  rows.length = 0;
  render();
  report('All examinations cleared.');
});
$('download').addEventListener('click', () => {
  const url = URL.createObjectURL(new Blob([exportCsv(rows)], { type: 'text/csv;charset=utf-8' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = 'ct-dose-summary.csv';
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  report('CSV exported locally.');
});
$('upload').addEventListener('change', async event => {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    if (file.size > 2 * 1024 * 1024) throw new Error('CSV must not exceed 2 MB.');
    const records = parseCsv(await file.text());
    const incoming = records.map((record, i) => {
      try {
        return {
          protocol: (record.protocol || ('Exam ' + (i + 1))).slice(0, 80),
          dose: calculateDose({
            ctdi: record.ctdi_vol_mgy, length: record.scan_length_cm,
            dlp: record.dlp_mgy_cm, k: record.k_msv_per_mgy_cm
          })
        };
      } catch (err) {
        throw new Error('CSV row ' + (i + 2) + ': ' + err.message);
      }
    });
    if (incoming.length + rows.length > 2000) throw new Error('Maximum of 2,000 examinations exceeded.');
    rows.push(...incoming);
    render();
    report(incoming.length + ' examinations imported locally.');
  } catch (err) {
    report(err.message, true);
  } finally {
    event.target.value = '';
  }
});
render();
