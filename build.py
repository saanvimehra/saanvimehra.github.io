#!/usr/bin/env python3
"""
build.py — converts essays/*.md to writing/*.html and rebuilds the writing list in index.html

Usage:
  python3 build.py        # build everything
  python3 build.py --push "your commit message"  # build + push to GitHub
"""

import os, re, sys, subprocess

ESSAYS_DIR = "essays"
OUTPUT_DIR = "writing"
INDEX_FILE = "index.html"

TOGGLE_SCRIPT = """
<script>
  const body = document.body;
  const btn = document.getElementById('toggle-btn');
  if (localStorage.getItem('mode') === 'light') {
    body.classList.add('light');
    btn.textContent = 'dark';
  }
  function toggleMode() {
    body.classList.toggle('light');
    const isLight = body.classList.contains('light');
    btn.textContent = isLight ? 'dark' : 'light';
    localStorage.setItem('mode', isLight ? 'light' : 'dark');
  }
</script>
"""

def parse_md(filepath):
    """Parse frontmatter and body from a markdown file."""
    with open(filepath) as f:
        content = f.read()

    # parse frontmatter
    meta = {"title": "", "date": ""}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = parts[2].strip()

    return meta, body

def md_to_html(text):
    """Minimal markdown to HTML — handles bold, italic, headings, paragraphs, hr."""
    lines = text.split("\n")
    html = []
    in_p = False

    def close_p():
        nonlocal in_p
        if in_p:
            html.append("</p>")
            in_p = False

    def inline(t):
        # bold
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        # italic
        t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
        # links
        t = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank">\1</a>', t)
        return t

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "---":
            close_p()
            html.append('<hr style="border:none;border-top:0.5px solid rgba(255,255,255,0.1);margin:2rem 0">')
        elif stripped.startswith("## "):
            close_p()
            html.append(f'<p style="font-style:italic;margin-top:2rem;margin-bottom:0.5rem">{inline(stripped[3:])}</p>')
        elif stripped == "":
            close_p()
        else:
            if not in_p:
                html.append("<p>")
                in_p = True
            else:
                html.append(" ")
            html.append(inline(stripped))

        i += 1

    close_p()
    return "\n".join(html)

def build_essay_html(meta, body_html):
    title = meta.get("title", "")
    date = meta.get("date", "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Saanvi Mehra</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0f0f0d;
    color: #e8e4d9;
    font-family: Times, 'Times New Roman', serif;
    font-size: 16px;
    line-height: 1.7;
    padding: 80px 0;
    transition: background 0.25s, color 0.25s;
  }}
  body.light {{
    background: #ffffff;
    color: #111111;
    font-family: Helvetica, Arial, sans-serif;
  }}
  .container {{ max-width: 780px; margin: 0 auto; padding: 0 48px; }}
  a {{ color: #5abf7a; text-decoration: underline; text-underline-offset: 3px; }}
  a:hover {{ color: #7dd494; }}
  p {{ text-align: justify; }}
  p + p {{ margin-top: 14px; }}
  .back {{ font-size: 14px; margin-bottom: 52px; display: block; }}
  .meta {{ font-size: 14px; margin-bottom: 8px; }}
  h1 {{ font-size: 24px; font-weight: 700; line-height: 1.3; margin-bottom: 48px; }}
  strong {{ font-weight: 700; }}
  .toggle-wrap {{ position: fixed; top: 28px; right: 36px; z-index: 100; }}
  .toggle {{
    background: none; border: none; cursor: pointer;
    font-size: 13px; color: #e8e4d9;
    text-decoration: underline; text-underline-offset: 3px;
    padding: 0; font-family: Times, 'Times New Roman', serif;
    transition: color 0.25s;
  }}
  body.light .toggle {{ color: #111111; font-family: Helvetica, Arial, sans-serif; }}
</style>
</head>
<body>

<div class="toggle-wrap">
  <button class="toggle" onclick="toggleMode()" id="toggle-btn">light</button>
</div>

<div class="container">
  <a class="back" href="/">← saanvimehra.com</a>
  <p class="meta">{date}</p>
  <h1>{title}</h1>
  {body_html}
</div>

{TOGGLE_SCRIPT}
</body>
</html>"""

def format_date_display(date_str):
    """Turn 2022-12 into Dec 2022, or pass through as-is."""
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    parts = date_str.split("-")
    if len(parts) == 2:
        try:
            m = int(parts[1])
            return f"{months[m-1]} {parts[0]}"
        except:
            pass
    return date_str

def rebuild_index(essays):
    """Rebuild the writing list in index.html."""
    with open(INDEX_FILE) as f:
        html = f.read()

    # build new writing list items
    items = []
    for e in sorted(essays, key=lambda x: x["date"], reverse=True):
        display_date = format_date_display(e["date"])
        slug = e["slug"]
        title = e["title"]
        items.append(f'      <li><span class="date">{display_date}</span><a href="writing/{slug}.html">{title}</a></li>')

    new_list = "\n".join(items)

    # replace everything between the ul tags in the writing section
    html = re.sub(
        r'(<ul class="writing-list">).*?(</ul>)',
        f'\\1\n{new_list}\n    \\2',
        html,
        flags=re.DOTALL
    )

    with open(INDEX_FILE, "w") as f:
        f.write(html)

    print(f"  ✓ updated writing list in {INDEX_FILE}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    essays = []

    for filename in os.listdir(ESSAYS_DIR):
        if not filename.endswith(".md"):
            continue

        slug = filename[:-3]
        filepath = os.path.join(ESSAYS_DIR, filename)
        meta, body = parse_md(filepath)
        body_html = md_to_html(body)
        page_html = build_essay_html(meta, body_html)

        out_path = os.path.join(OUTPUT_DIR, f"{slug}.html")
        with open(out_path, "w") as f:
            f.write(page_html)

        print(f"  ✓ built writing/{slug}.html  ({meta['title']})")
        essays.append({"slug": slug, "title": meta["title"], "date": meta["date"]})

    rebuild_index(essays)

    # optionally push
    if len(sys.argv) >= 2 and sys.argv[1] == "--push":
        msg = sys.argv[2] if len(sys.argv) >= 3 else "update essays"
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", msg])
        subprocess.run(["git", "push", "origin", "main"])
        print(f"\n  ✓ pushed — live in ~30 seconds")

if __name__ == "__main__":
    main()
