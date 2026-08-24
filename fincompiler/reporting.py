from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def _cell(value: Any) -> str:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return html.escape("" if value is None else str(value))


def _table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    if not rows:
        return '<p class="empty">No items.</p>'
    header = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{_cell(row.get(key))}</td>" for key, _ in columns) + "</tr>"
        for row in rows
    )
    return f"<div class=\"table-wrap\"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>"


def render_management_pack_html(report: dict[str, Any]) -> str:
    readiness = report["output_readiness"]
    ready_class = "ready" if readiness == "READY" else "blocked"
    workflow = report["close_workflow"]
    recon = report["reconciliation"]
    pvm = report["pvm"]
    fx = report["fx"]
    manifest = report["run_manifest"]
    tasks = workflow["tasks"]
    exceptions = report["exceptions"]
    causes = recon.get("causes", [])
    segments = pvm.get("segments", [])
    applications = fx.get("applications", [])
    sources = manifest.get("sources", [])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FinCompiler Management Pack · {_cell(manifest['run_id'])}</title>
<style>
:root{{--navy:#14233c;--blue:#225ea8;--gold:#e4ad3a;--ink:#172033;--muted:#657086;--line:#dce2ea;--paper:#fff;--bg:#f4f6f9;--red:#a12622;--green:#176b3a}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 Arial,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:32px 24px 64px}} header{{background:var(--navy);color:#fff;padding:28px;border-radius:14px}}
h1{{margin:0 0 6px;font-size:30px}} h2{{margin:30px 0 12px;font-size:20px}} .subtitle{{color:#dbe5f3}}
.badge{{display:inline-block;margin-top:16px;padding:8px 12px;border-radius:999px;font-weight:700}} .badge.ready{{background:#dff4e7;color:var(--green)}} .badge.blocked{{background:#fde5e3;color:var(--red)}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:16px}} .card{{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:16px}}
.label{{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em}} .value{{font-size:22px;font-weight:700;margin-top:4px}}
.table-wrap{{overflow-x:auto;background:var(--paper);border:1px solid var(--line);border-radius:10px}} table{{width:100%;border-collapse:collapse}} th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} th{{background:#eef2f7;color:#354056;font-size:12px}} tr:last-child td{{border-bottom:0}}
.notice{{padding:12px 14px;border-left:4px solid var(--gold);background:#fff8e8}} .empty{{color:var(--muted)}} footer{{margin-top:32px;color:var(--muted);font-size:12px}}
@media(max-width:760px){{.grid{{grid-template-columns:1fr 1fr}} main{{padding:16px}}}}
@media print{{body{{background:#fff}} main{{max-width:none;padding:0}} .card,.table-wrap{{break-inside:avoid}}}}
</style>
</head>
<body><main>
<header><h1>FinCompiler Management Pack</h1><div class="subtitle">Local-first deterministic month-end evidence · Run {_cell(manifest['run_id'])}</div><span class="badge {ready_class}">{_cell(readiness)}</span></header>
<div class="grid">
<div class="card"><div class="label">Controls complete</div><div class="value">{workflow['completed_tasks']} / {workflow['total_tasks']}</div></div>
<div class="card"><div class="label">Blocking items</div><div class="value">{len(exceptions)}</div></div>
<div class="card"><div class="label">Sales / GL difference</div><div class="value">{_cell(recon['variance'])}</div></div>
<div class="card"><div class="label">Base currency</div><div class="value">{_cell(fx['base_currency'])}</div></div>
</div>
<p class="notice">FinCompiler does not create balancing entries, silently approve uncertain mappings or replace Finance review.</p>
<h2>Month-end action plan</h2>
{_table(tasks, [('question','Question'),('status','Status'),('outcome','Outcome'),('next_action','Next action')])}
<h2>Blocking control items</h2>
{_table(exceptions, [('severity','Severity'),('code','Code'),('message','Message'),('context','Evidence')])}
<h2>Sales vs GL investigator</h2>
<div class="grid">
<div class="card"><div class="label">Sales</div><div class="value">{_cell(recon['sales_total']['value'])}</div></div>
<div class="card"><div class="label">GL revenue</div><div class="value">{_cell(recon['gl_total']['value'])}</div></div>
<div class="card"><div class="label">Difference</div><div class="value">{_cell(recon['variance'])}</div></div>
<div class="card"><div class="label">Status</div><div class="value">{_cell(recon['status'])}</div></div>
</div>
{_table(causes, [('reference','Reference'),('reason','Cause'),('sales','Sales'),('gl','GL'),('difference','Difference')])}
<h2>Budget vs Actual / PVM</h2>
<div class="grid">
<div class="card"><div class="label">Variance</div><div class="value">{_cell(pvm['totals'].get('variance','0.00'))}</div></div>
<div class="card"><div class="label">Volume</div><div class="value">{_cell(pvm['totals'].get('volume','0.00'))}</div></div>
<div class="card"><div class="label">Price</div><div class="value">{_cell(pvm['totals'].get('price','0.00'))}</div></div>
<div class="card"><div class="label">Bridge check</div><div class="value">{_cell(pvm['totals']['bridge_check'])}</div></div>
</div>
{_table(segments, [('customer','Customer'),('sku','SKU'),('actual_revenue','Actual'),('budget_revenue','Budget'),('variance','Variance'),('volume','Volume'),('price','Price'),('mix_residual','Mix / residual')])}
<h2>Applied exchange-rate evidence</h2>
{_table(applications, [('dataset','Dataset'),('record_id','Record'),('source_currency','From'),('target_currency','To'),('effective_date','Rate date'),('rate','Rate'),('method','Method'),('formula','Formula'),('observations','Evidence')])}
<h2>Source files and integrity hashes</h2>
{_table(sources, [('dataset','Dataset'),('file','Local file'),('bytes','Bytes'),('sha256','SHA-256')])}
<footer>Generated by FinCompiler engine {_cell(manifest['engine_version'])}. Created {_cell(manifest['created_at_utc'])}. Full row-level lineage remains in the local SQLite evidence store.</footer>
</main></body></html>"""


def write_management_pack_html(output_dir: str | Path, report: dict[str, Any]) -> Path:
    path = Path(output_dir) / "management_pack.html"
    path.write_text(render_management_pack_html(report), encoding="utf-8")
    return path
