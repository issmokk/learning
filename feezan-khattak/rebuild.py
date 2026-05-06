#!/usr/bin/env python3
"""Rebuild feezan-khattak/index.html from posts_state.json + images/.
Used by the scheduled refresh task."""
import json, html, re, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, 'posts_state.json')
IMG_DIR = os.path.join(HERE, 'images')
OUT = os.path.join(HERE, 'index.html')

with open(STATE) as f:
    state = json.load(f)
posts = state['posts']
local_images = {fn[:-4] for fn in os.listdir(IMG_DIR) if fn.endswith('.jpg')} if os.path.isdir(IMG_DIR) else set()

def esc(s): return html.escape(s or '', quote=True)
def fmt_caption(s):
    s = s or ''
    s = re.sub(r'\n+\s*#[A-Za-z]+(\s+#[A-Za-z]+)+\s*$', '', s)
    lines = s.split('\n')
    return lines[0].strip(), '\n'.join(lines[1:]).strip()
def fmt_body(s):
    if not s: return ''
    s = esc(s)
    s = re.sub(r'\n{2,}', '</p><p>', s)
    s = s.replace('\n', '<br>')
    return '<p>' + s + '</p>'

CSS = """
:root { --bg: #0e1116; --panel: #161b22; --border: #30363d; --text: #e6edf3; --muted: #8b949e; --accent: #58a6ff; --accent-soft: #1f6feb; --feezan: #f7c948; --feezan-bg: rgba(247, 201, 72, 0.08); }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; line-height: 1.55; font-size: 15px; }
.wrap { max-width: 880px; margin: 0 auto; padding: 40px 24px 80px; }
.top h1 { font-size: 28px; margin: 0 0 8px 0; letter-spacing: -0.02em; }
.top .subtitle { color: var(--muted); margin: 0 0 8px 0; }
.top .meta { color: var(--muted); font-size: 13px; margin-bottom: 28px; }
.top .meta a { color: var(--accent); }
.toc { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px 20px; margin-bottom: 32px; }
.toc h3 { margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); }
.toc ol { margin: 0; padding-left: 20px; columns: 2; column-gap: 24px; }
.toc li { margin: 4px 0; break-inside: avoid; }
.toc a { color: var(--text); text-decoration: none; font-size: 14px; }
.toc a:hover { color: var(--accent); }
.post { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 28px; margin-bottom: 28px; scroll-margin-top: 24px; }
.post header { display: flex; align-items: flex-start; gap: 16px; margin-bottom: 18px; }
.post .num { background: var(--accent-soft); color: white; font-weight: 600; border-radius: 6px; padding: 6px 10px; font-size: 13px; flex-shrink: 0; }
.post .title-block { flex: 1; }
.post h2 { margin: 0; font-size: 22px; letter-spacing: -0.01em; }
.post .date { color: var(--muted); font-size: 13px; }
.post figure { margin: 0 0 20px 0; background: white; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
.post img.diagram { display: block; width: 100%; height: auto; }
.no-img-note { background: rgba(139, 148, 158, 0.1); border: 1px dashed var(--border); border-radius: 6px; padding: 10px 14px; color: var(--muted); font-size: 13px; margin-bottom: 16px; }
.post .caption p { margin: 0 0 12px 0; }
.post .caption { font-size: 15px; }
.post .examples { margin-top: 20px; padding-top: 18px; border-top: 1px solid var(--border); }
.post .examples h3 { margin: 0 0 10px 0; font-size: 13px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--feezan); }
.post blockquote.feezan { margin: 0 0 12px 0; padding: 12px 16px; background: var(--feezan-bg); border-left: 3px solid var(--feezan); border-radius: 4px; font-size: 14px; }
.post blockquote.feezan p { margin: 0 0 8px 0; }
.post .other-comments { margin-top: 16px; font-size: 14px; }
.post .other-comments summary { cursor: pointer; color: var(--muted); padding: 6px 0; font-size: 13px; }
.post .other-comments summary:hover { color: var(--accent); }
.post .other-comments blockquote { margin: 8px 0; padding: 10px 14px; background: rgba(139, 148, 158, 0.06); border-left: 2px solid var(--border); border-radius: 4px; }
.post .other-comments blockquote p { margin: 0 0 6px 0; }
.post .src-link { display: inline-block; margin-top: 18px; color: var(--accent); text-decoration: none; font-size: 13px; }
.post .src-link:hover { text-decoration: underline; }
"""

# Sort posts newest first by id (numeric)
posts_sorted = sorted(posts, key=lambda p: int(p['id']), reverse=True)

toc_items = []
for i, p in enumerate(posts_sorted, 1):
    title, _ = fmt_caption(p['cap'])
    toc_items.append(f'    <li><a href="#post-{p["id"]}">{esc(title)}</a></li>')
toc_html = '\n'.join(toc_items)

sections = []
for i, p in enumerate(posts_sorted, 1):
    title, body = fmt_caption(p['cap'])
    fc = [c for c in p.get('fc', []) if c and c.strip()]
    oc = [c for c in p.get('oc', []) if c and c.get('t', '').strip()]
    has_img = p['id'] in local_images
    s = f'<section class="post" id="post-{p["id"]}">\n'
    s += f'  <header><span class="num">{i:02d}</span><div class="title-block"><h2>{esc(title)}</h2><span class="date">{esc(p["date"])} ago</span></div></header>\n'
    if has_img:
        s += f'  <figure><img class="diagram" src="images/{p["id"]}.jpg" alt="{esc(title)}" loading="lazy" /></figure>\n'
    else:
        s += '  <div class="no-img-note">No diagram on this post (text-only)</div>\n'
    s += f'  <div class="caption">{fmt_body(body)}</div>\n'
    if fc:
        s += '  <div class="examples"><h3>Feezan in comments</h3>'
        for c in fc:
            s += f'<blockquote class="feezan">{fmt_body(c)}</blockquote>'
        s += '</div>\n'
    meaningful = [c for c in oc if len(c.get('t', '').strip()) > 50]
    if meaningful:
        s += f'  <details class="other-comments"><summary>{len(meaningful)} community comment(s) — real-world examples</summary>'
        for c in meaningful:
            author = c.get('a', '').strip() or 'Reader'
            s += f'<blockquote><strong>{esc(author)}:</strong> {fmt_body(c["t"])}</blockquote>'
        s += '</details>\n'
    s += f'  <a class="src-link" href="https://www.linkedin.com/feed/update/urn:li:activity:{p["id"]}/" target="_blank" rel="noopener">View original post on LinkedIn ↗</a>\n'
    s += '</section>\n'
    sections.append(s)

doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Feezan Khattak — Backend & Payments Learning Library</title>
<style>{CSS}</style></head><body><div class="wrap">
<div class="top">
<h1>Feezan Khattak — Backend & Payments Learning Library</h1>
<p class="subtitle">Hand-drawn system design diagrams, one concept per section.</p>
<p class="meta">{len(posts_sorted)} posts collected from <a href="https://www.linkedin.com/in/feezan-khattak/recent-activity/all/" target="_blank">linkedin.com/in/feezan-khattak</a></p>
</div>
<nav class="toc"><h3>Concepts covered</h3><ol>
{toc_html}
</ol></nav>
{''.join(sections)}
</div></body></html>
"""

with open(OUT, 'w') as f:
    f.write(doc)
print(f'Wrote {OUT} ({len(doc)} chars, {len(posts_sorted)} posts, {sum(1 for p in posts_sorted if p["id"] in local_images)} with images)')
