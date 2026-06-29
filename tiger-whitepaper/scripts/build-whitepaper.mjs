#!/usr/bin/env node
/**
 * Tiger Claw branded white-paper builder.
 *
 * Generates the standardized "signature": a dark branded cover, an optional
 * numbered/signable confidentiality receipt (light page), then the body the
 * agent authored, and renders the whole thing to a print-ready PDF via headless
 * Chrome. The cover + receipt are generated HERE so numbering and the receipt
 * stay identical across every paper. The body is authored by the agent as an
 * HTML fragment using the documented classes (see REFERENCE.md).
 *
 * Usage:  node build-whitepaper.mjs <spec.json>
 * Paths inside the spec (bodyHtmlPath) are resolved relative to the spec file.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, isAbsolute, resolve as pathResolve } from 'node:path';

const specPath = process.argv[2];
if (!specPath) {
  console.error('usage: node build-whitepaper.mjs <spec.json>');
  process.exit(1);
}
const spec = JSON.parse(readFileSync(specPath, 'utf8'));
const baseDir = dirname(specPath);
// Always return ABSOLUTE paths — Chrome's file:// URL and --print-to-pdf both require them.
const resolve = (p) => (isAbsolute(p) ? p : pathResolve(baseDir, p));

const KICKERS = {
  science: 'Scientific White Paper',
  technology: 'Technology White Paper',
  marketing: 'Marketing White Paper',
};

const esc = (s = '') => String(s);
const num = esc(spec.controlNumber || '001');
const entity = esc(spec.entity || 'Mariah Marketing LLC');
const author = esc(spec.author || 'Brent Bryson');
const date = esc(spec.date || '');
const tagline = esc(spec.tagline || 'Fortune is in the follow-up.');
const kicker = esc(spec.kicker || KICKERS[spec.variation] || 'White Paper');
const confidential = spec.confidential !== false;
const stamp = `${confidential ? 'Confidential · ' : ''}No. ${num}`;

const CLAW = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0A0A0A" stroke-width="2.4"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>`;

const coverMeta =
  spec.coverMeta ||
  [
    { label: spec.recipientLabel || 'Prepared for', val: spec.recipient || '' },
    { label: 'From', val: author },
    { label: 'Date', val: date },
    { label: 'Issued by', val: entity },
  ].filter((m) => m.val);

function coverHtml() {
  return `
<section class="sheet dark cover">
  <div class="cover-top"><span class="mark">${CLAW}</span><span class="wordmark">TIGER CLAW</span></div>
  <div class="cover-rule"></div>
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span class="eyebrow">${kicker}</span>
    ${confidential || num ? `<span class="stamp"><span class="dot"></span> ${stamp}</span>` : ''}
  </div>
  <h1 class="cover-title">${spec.title || ''}</h1>
  ${spec.subtitle ? `<p class="cover-sub">${spec.subtitle}</p>` : ''}
  <div class="cover-meta">
    ${coverMeta.map((m) => `<div><div class="label">${esc(m.label)}</div><div class="val">${esc(m.val)}</div></div>`).join('\n')}
  </div>
  <div class="cover-foot"><span class="tag">${tagline}</span><span class="ent">Tiger Claw · ${entity}</span></div>
</section>`;
}

function receiptHtml() {
  const r = spec.receipt || {};
  const issuedTo = esc(r.issuedTo || spec.recipient || '');
  const clauseTitle = esc(r.clauseTitle || 'Acknowledgment of confidentiality.');
  const clauseBody =
    r.clauseBody ||
    `By signing, I, the named recipient, agree that the contents of Tiger Claw White Paper No. ${num} — including the product, the method, the commercial arrangement, and any related conversations — are confidential and proprietary to ${author} and ${entity}. I will not copy, forward, publish, or disclose any part of it to any third party without prior written permission, and I will use it solely to evaluate the opportunity offered to me. This receipt confirms my acceptance and my receipt of the document.`;
  const note =
    r.note ||
    'This is a good-faith acknowledgment meant to keep an early-stage opportunity private while we talk.';
  const returnEmail = esc(r.returnEmail || 'support@tigerclaw.io');
  return `
<section class="sheet light" style="padding:14mm 19mm 12mm;">
  <div class="rcpt-head">
    <span class="wordmark">TIGER CLAW</span>
    <div class="rcpt-no"><div class="n">No. ${num}</div><div class="l">White Paper Control</div></div>
  </div>
  <h1 class="rcpt-title">CONFIDENTIALITY RECEIPT</h1>
  <div class="rcpt-meta">
    <div><div class="k">Issued to</div><div class="v">${issuedTo}</div></div>
    <div><div class="k">Issued by</div><div class="v">${author} · ${entity}</div></div>
    <div><div class="k">Document</div><div class="v">Tiger Claw White Paper No. ${num}</div></div>
    <div><div class="k">Date issued</div><div class="v">${date}</div></div>
  </div>
  <div class="rcpt-body">
    <p>This document and the opportunity it describes are shared with you in confidence. Before reading further, please review and sign below, then return this page as instructed.</p>
    <div class="clause"><strong>${clauseTitle}</strong> ${clauseBody}</div>
    <p>${note}</p>
  </div>
  <div class="sigblock">
    <div><div class="sigline"></div><div class="sigcap">Signature</div></div>
    <div><div class="sigline"></div><div class="sigcap">Date</div></div>
  </div>
  <div class="sigblock" style="margin-top:4mm;">
    <div><div class="sigline"></div><div class="sigcap">Printed name</div></div>
    <div></div>
  </div>
  <div class="return"><div class="h">Sign and return by email to</div><div class="a">${returnEmail}</div></div>
  <div class="rcpt-foot"><span>Tiger Claw White Paper No. ${num}</span><span>Confidential · Page 2</span></div>
</section>`;
}

const body = spec.bodyHtmlPath ? readFileSync(resolve(spec.bodyHtmlPath), 'utf8') : '';

const html = `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><style>${CSS()}</style></head><body>
${coverHtml()}
${spec.receipt && spec.receipt.include !== false ? receiptHtml() : ''}
${body}
</body></html>`;

const tmpHtml = resolve('.whitepaper.build.html');
writeFileSync(tmpHtml, html);

const outPath = resolve(spec.outPath || 'whitepaper.pdf');
const CHROME =
  spec.chromePath || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
execFileSync(
  CHROME,
  [
    '--headless=new',
    '--disable-gpu',
    '--no-pdf-header-footer',
    '--virtual-time-budget=20000',
    '--run-all-compositor-stages-before-draw',
    `--print-to-pdf=${outPath}`,
    `file://${tmpHtml}`,
  ],
  { stdio: 'inherit' }
);
console.log('Wrote', outPath);

function CSS() {
  return `
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { margin: 0; padding: 0; }
body { font-family: 'Space Grotesk', system-ui, sans-serif; }
@page { size: Letter; margin: 0; }
.sheet { width: 8.5in; min-height: 11in; padding: 17mm 19mm; page-break-after: always; position: relative; overflow: hidden; }
.sheet:last-child { page-break-after: auto; }
.dark  { background: #0A0A0A; color: #c9c9d2; }
.light { background: #ffffff; color: #1c1c1c; }
.eyebrow { font-family: 'IBM Plex Mono', monospace; font-size: 10.5pt; letter-spacing: 0.22em; text-transform: uppercase; color: #E8722A; }
.eyebrow.dim { color: #6b6b75; }
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; font-weight: 400; letter-spacing: 0.02em; margin: 0; line-height: 0.98; }
.dark strong, .dark b { color: #ffffff; font-weight: 600; }
.light strong, .light b { color: #0A0A0A; font-weight: 600; }
.orange { color: #E8722A; }
.green  { color: #22C55E; }
.wordmark { font-family: 'Bebas Neue', sans-serif; letter-spacing: 0.10em; }
.mark { width: 46px; height: 46px; border-radius: 999px; background: #E8722A; display: inline-flex; align-items: center; justify-content: center; }
.cover { display: flex; flex-direction: column; }
.cover-top { display: flex; align-items: center; gap: 14px; }
.cover-top .wordmark { font-size: 30pt; color: #ffffff; }
.cover-rule { height: 1px; background: rgba(255,255,255,0.10); margin: 9mm 0; }
.cover-title { font-size: 64pt; color: #ffffff; margin-top: 4mm; }
.cover-sub { font-size: 15pt; color: #a1a1aa; margin-top: 6mm; max-width: 150mm; line-height: 1.45; }
.cover-meta { margin-top: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 7mm 0; }
.cover-meta .label { font-family: 'IBM Plex Mono', monospace; font-size: 9pt; letter-spacing: 0.18em; text-transform: uppercase; color: #6b6b75; }
.cover-meta .val { font-size: 13.5pt; color: #ffffff; margin-top: 2mm; }
.cover-foot { margin-top: 9mm; padding-top: 6mm; border-top: 1px solid rgba(255,255,255,0.10); display:flex; justify-content: space-between; align-items:center; }
.cover-foot .tag { font-family:'Bebas Neue',sans-serif; font-size: 18pt; letter-spacing:0.04em; color:#E8722A; }
.cover-foot .ent { font-family:'IBM Plex Mono',monospace; font-size: 8.5pt; letter-spacing:0.14em; text-transform:uppercase; color:#6b6b75; }
.stamp { display:inline-flex; align-items:center; gap:8px; border:1px solid rgba(232,114,42,0.45); border-radius: 999px; padding: 5px 13px; font-family:'IBM Plex Mono',monospace; font-size: 9pt; letter-spacing:0.18em; text-transform:uppercase; color:#E8722A; }
.dot { width:8px; height:8px; border-radius:999px; background:#E8722A; display:inline-block; }
.dot.green { background:#22C55E; }
.rcpt-head { display:flex; justify-content:space-between; align-items:flex-start; border-bottom: 2px solid #0A0A0A; padding-bottom: 6mm; }
.rcpt-head .wordmark { font-size: 24pt; color:#0A0A0A; }
.rcpt-no { text-align:right; }
.rcpt-no .n { font-family:'Bebas Neue',sans-serif; font-size: 30pt; color:#E8722A; line-height:0.9; }
.rcpt-no .l { font-family:'IBM Plex Mono',monospace; font-size: 8.5pt; letter-spacing:0.18em; text-transform:uppercase; color:#6b6b75; }
.rcpt-title { font-size: 34pt; color:#0A0A0A; margin-top: 5mm; }
.rcpt-meta { display:grid; grid-template-columns: 1fr 1fr; gap: 3mm 0; margin: 5mm 0; font-size: 11pt; }
.rcpt-meta .k { font-family:'IBM Plex Mono',monospace; font-size: 8.5pt; letter-spacing:0.14em; text-transform:uppercase; color:#6b6b75; }
.rcpt-meta .v { font-size: 12.5pt; color:#0A0A0A; margin-top:1mm; }
.rcpt-body { font-size: 11.5pt; line-height: 1.5; color:#2a2a2a; }
.rcpt-body p { margin: 0 0 3.5mm 0; }
.clause { background:#f5f5f4; border-left: 3px solid #E8722A; padding: 4mm 6mm; margin: 4mm 0; font-size: 11pt; line-height:1.48; }
.sigblock { margin-top: 6mm; display:grid; grid-template-columns: 1.4fr 1fr; gap: 10mm; }
.sigline { border-bottom: 1.5px solid #0A0A0A; height: 10mm; }
.sigcap { font-family:'IBM Plex Mono',monospace; font-size: 8.5pt; letter-spacing:0.14em; text-transform:uppercase; color:#6b6b75; margin-top: 2mm; }
.return { margin-top: 6mm; background:#0A0A0A; color:#fff; border-radius: 8px; padding: 5mm 6mm; }
.return .h { font-family:'IBM Plex Mono',monospace; font-size: 9pt; letter-spacing:0.18em; text-transform:uppercase; color:#E8722A; }
.return .a { font-size: 14pt; color:#fff; margin-top: 2mm; font-weight:600; }
.rcpt-foot { position:absolute; bottom: 14mm; left:19mm; right:19mm; border-top:1px solid #e5e5e5; padding-top:4mm; font-family:'IBM Plex Mono',monospace; font-size:8pt; letter-spacing:0.12em; text-transform:uppercase; color:#9a9a9a; display:flex; justify-content:space-between; }
.body-head { display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:5mm; margin-bottom: 9mm; }
.body-head .wordmark { font-size: 17pt; color:#fff; letter-spacing:0.10em; }
.body-head .pg { font-family:'IBM Plex Mono',monospace; font-size:8.5pt; letter-spacing:0.16em; text-transform:uppercase; color:#6b6b75; }
.sec { margin-bottom: 8.5mm; }
.sec-label { display:flex; align-items:center; gap: 10px; margin-bottom: 4mm; }
.sec-label .num { font-family:'IBM Plex Mono',monospace; font-size:10pt; color:#E8722A; letter-spacing:0.12em; }
.sec-label .ln { height:1px; flex:1; background:rgba(255,255,255,0.10); }
.sec h2 { font-size: 27pt; color:#ffffff; margin-bottom: 4mm; }
.sec p { font-size: 12.6pt; line-height: 1.62; color:#c4c4ce; margin: 0 0 3.5mm 0; }
.lead { font-size: 14pt !important; color:#e9e9ee !important; }
.card { border:1px solid rgba(232,114,42,0.28); background: rgba(232,114,42,0.05); border-radius: 12px; padding: 6mm 7mm; margin: 5mm 0; }
.card .q { font-size: 14.5pt; line-height:1.5; color:#ffffff; font-weight:500; }
.chips { display:flex; flex-wrap:wrap; gap: 7px; margin: 4mm 0 2mm; }
.chip { display:inline-flex; align-items:center; gap:7px; border:1px solid rgba(255,255,255,0.12); border-radius:999px; padding: 4px 11px; font-family:'IBM Plex Mono',monospace; font-size:8.5pt; letter-spacing:0.12em; text-transform:uppercase; color:#c9c9d2; }
.sec table { width:100%; border-collapse:collapse; margin:4mm 0; font-size:10.8pt; }
.sec th { text-align:left; font-family:'IBM Plex Mono',monospace; font-size:8.5pt; letter-spacing:0.1em; text-transform:uppercase; color:#E8722A; border-bottom:1px solid rgba(232,114,42,0.30); padding:3mm; }
.sec td { color:#c4c4ce; border-bottom:1px solid rgba(255,255,255,0.06); padding:3mm; vertical-align:top; }
.refs { font-size:9.5pt; color:#9a9aa3; line-height:1.5; padding-left: 5mm; }
.refs li { margin-bottom:2mm; }
.cta { border:1px solid rgba(232,114,42,0.45); border-radius: 14px; background: linear-gradient(180deg, rgba(232,114,42,0.10), rgba(232,114,42,0.02)); padding: 8mm; margin-top: 4mm; }
.cta .step { font-size: 13pt; line-height:1.6; color:#e9e9ee; margin: 0 0 3mm 0; }
.cta .pill { display:inline-block; margin-top: 4mm; background:#E8722A; color:#0A0A0A; font-weight:700; font-size: 13pt; padding: 9px 26px; border-radius: 999px; }
.endtag { margin-top: 8mm; padding-top:5mm; border-top:1px solid rgba(255,255,255,0.08); font-family:'Bebas Neue',sans-serif; font-size: 20pt; letter-spacing:0.04em; color:#E8722A; }
`;
}
