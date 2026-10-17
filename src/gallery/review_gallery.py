"""
Visual Review Gallery Generator.
Generates an interactive, responsive HTML gallery displaying evaluated photographs,
claimed state & category, source provenance, license status, visual filter verdicts,
and explicit failure/quarantine reasons.
"""

from pathlib import Path
from typing import List, Dict, Any
import html

from src.config import REPORTS_DIR


def generate_html_review_gallery(
    audit_records: List[Dict[str, Any]],
    output_path: Path = REPORTS_DIR / "review_gallery.html"
) -> Path:
    """Generate an aesthetic review gallery HTML page."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cards_html = []
    for rec in audit_records:
        decision = rec.get("final_decision", "UNVERIFIED")
        badge_color = {
            "APPROVED": "#10b981",    # Emerald
            "QUARANTINE": "#f59e0b",  # Amber
            "REJECTED": "#ef4444",    # Rose/Red
            "UNVERIFIED": "#6b7280"   # Gray
        }.get(decision, "#6b7280")

        img_path = rec.get("image_path", "")
        # Relativize image path for browser viewing if possible
        try:
            rel_src = Path(img_path).resolve().as_uri()
        except Exception:
            rel_src = img_path

        state = html.escape(str(rec.get("claimed_state", "Unknown")))
        cat = html.escape(str(rec.get("claimed_category", "Unknown")))
        concept = html.escape(str(rec.get("claimed_concept", "")))
        reason = html.escape(str(rec.get("rejection_or_warning_reason", "N/A")))
        source_url = html.escape(str(rec.get("source_page_url", "")))
        lic = html.escape(str(rec.get("license_name", "Unknown")))
        creator = html.escape(str(rec.get("creator", "Unknown")))

        # Quality metrics
        tq = rec.get("technical_quality", {})
        width = tq.get("width", 0)
        height = tq.get("height", 0)
        blur = tq.get("blur_score", 0.0)

        card = f"""
        <div class="card" style="border-top: 4px solid {badge_color};">
            <div class="image-wrapper">
                <img src="{rel_src}" alt="{concept}" loading="lazy" onerror="this.src='https://via.placeholder.com/400x300?text=Preview+Unavailable'">
                <span class="badge" style="background-color: {badge_color};">{decision}</span>
            </div>
            <div class="card-content">
                <div class="tags">
                    <span class="tag tag-state">{state}</span>
                    <span class="tag tag-cat">{cat}</span>
                </div>
                <h3 class="concept-title">{concept or "Unnamed Object"}</h3>
                <div class="meta-row"><strong>Dimensions:</strong> {width} x {height} px</div>
                <div class="meta-row"><strong>Sharpness (Laplacian):</strong> {blur:.1f}</div>
                <div class="meta-row"><strong>Licence:</strong> {lic}</div>
                <div class="meta-row"><strong>Creator:</strong> {creator}</div>
                <div class="meta-row"><strong>Source:</strong> <a href="{source_url}" target="_blank" rel="noopener">Source Link</a></div>
                <div class="reason-box" style="background: rgba({int(badge_color[1:3], 16)}, {int(badge_color[3:5], 16)}, {int(badge_color[5:7], 16)}, 0.1);">
                    <strong>Outcome Reason:</strong> {reason}
                </div>
            </div>
        </div>
        """
        cards_html.append(card)

    total_count = len(audit_records)
    approved_count = sum(1 for r in audit_records if r.get("final_decision") == "APPROVED")
    quarantined_count = sum(1 for r in audit_records if r.get("final_decision") in ["QUARANTINE", "UNVERIFIED"])
    rejected_count = sum(1 for r in audit_records if r.get("final_decision") == "REJECTED")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IndiaCulFair — Image Audit & Verification Gallery</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border: #334155;
            --accent: #38bdf8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text-primary);
            padding: 2rem;
        }}
        header {{
            max-width: 1400px;
            margin: 0 auto 2rem auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1.5rem;
        }}
        h1 {{ font-size: 1.8rem; font-weight: 700; color: #fff; }}
        .stats-bar {{
            display: flex;
            gap: 1rem;
        }}
        .stat-badge {{
            padding: 0.5rem 1rem;
            border-radius: 8px;
            background: var(--surface);
            font-weight: 600;
            border: 1px solid var(--border);
        }}
        .grid {{
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1.5rem;
        }}
        .card {{
            background: var(--surface);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            transition: transform 0.2s ease;
        }}
        .card:hover {{ transform: translateY(-4px); }}
        .image-wrapper {{
            position: relative;
            height: 220px;
            background: #000;
            overflow: hidden;
        }}
        .image-wrapper img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .badge {{
            position: absolute;
            top: 12px;
            right: 12px;
            color: #fff;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}
        .card-content {{
            padding: 1.2rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            flex-grow: 1;
        }}
        .tags {{
            display: flex;
            gap: 0.5rem;
        }}
        .tag {{
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .tag-state {{ background: #0369a1; color: #e0f2fe; }}
        .tag-cat {{ background: #4338ca; color: #e0e7ff; }}
        .concept-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #fff;
            margin: 0.2rem 0;
        }}
        .meta-row {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        .meta-row a {{
            color: var(--accent);
            text-decoration: none;
        }}
        .reason-box {{
            margin-top: auto;
            padding: 0.75rem;
            border-radius: 6px;
            font-size: 0.8rem;
            line-height: 1.4;
            color: #f1f5f9;
        }}
    </style>
</head>
<body>
    <header>
        <div>
            <h1>IndiaCulFair — Image Audit & Verification Gallery</h1>
            <p style="color: var(--text-secondary); margin-top: 4px;">Rigorous 10-Gate Validation across 7 States & 7 Categories</p>
        </div>
        <div class="stats-bar">
            <div class="stat-badge">Total Evaluated: {total_count}</div>
            <div class="stat-badge" style="color: #10b981;">Approved: {approved_count}</div>
            <div class="stat-badge" style="color: #f59e0b;">Quarantine: {quarantined_count}</div>
            <div class="stat-badge" style="color: #ef4444;">Rejected: {rejected_count}</div>
        </div>
    </header>

    <div class="grid">
        {"".join(cards_html) if cards_html else "<p style='color: var(--text-secondary);'>No evaluated images available yet.</p>"}
    </div>
</body>
</html>
"""
    output_path.write_text(html_content, encoding="utf-8")
    print(f"Generated visual review gallery at: {output_path}")
    return output_path
