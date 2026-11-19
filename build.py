#!/usr/bin/env python3
"""Render the garden. An optional Obsidian vault supplies explicitly published notes."""
import argparse
import calendar
import json
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
BRANCHES = {
    "Reading": ("Books, poems, and passages.", 14.4, 20.7),
    "Writing": ("Essays and letters.", 42.2, 42.8),
    "Hinduism": ("Scripture, practice, and consciousness.", 70.5, 30.8),
    "Work": ("Payments, code, and intersection sets.", 88.9, 56.0),
    "Roots": ("Noida, family, and the things that stick.", 17.1, 59.5),
    "Music": ("Things to listen to.", 73.6, 74.4),
}
WIKI = re.compile(r'\[\[([^\]\n]+)\]\]')
INLINE = re.compile(r'\[\[[^\]\n]+\]\]|\[[^\]\n]+\]\([^\s)]+\)|\*\*[^*\n]+\*\*|\*[^*\n]+\*|`[^`\n]+`')
GENERATED = '<!-- Built by the mango notebook. -->'
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')


@dataclass
class Note:
    slug: str
    title: str
    branch: str
    kind: str
    date: str
    body: str
    source: str
    filename: str

    @property
    def url(self):
        return ('writing/' if self.source == 'essays' else 'notes/') + self.slug + '.html'

    @property
    def date_label(self):
        if not self.date:
            return ''
        year, month, *_ = self.date.split('-')
        return f'{calendar.month_abbr[int(month)]} {year}'


def parse(path):
    text = path.read_text(encoding='utf-8')
    header = re.match(r'\A---\n(.*?)\n---(?:\n|$)', text, re.S)
    if not header:
        return {}, text
    fields = {}
    for line in header[1].splitlines():
        if ':' in line and not line.startswith((' ', '\t')):
            k, v = line.split(':', 1)
            v = v.strip()
            if v.startswith('"') and v.endswith('"'):
                v = json.loads(v)
            elif len(v) >= 2 and v[0] == "'" and v[-1] == "'":
                v = v[1:-1]
            fields[k.strip()] = v
    return fields, text[header.end():].strip()


def read_notes(vault=None):
    if vault:
        if not (vault / '.mango-vault').is_file() or not (vault / 'Tree').is_dir():
            raise ValueError('Choose your Mango notebook vault, containing the Tree folder.')
        tree = vault / 'Tree'
        if tree.is_symlink():
            raise ValueError('The public Tree folder must be inside this vault.')
        inputs = (p for p in sorted(tree.rglob('*.md'))
                  if not p.is_symlink() and tree.resolve() in p.resolve().parents)
    else:
        inputs = [p for folder in ('essays', 'notebook') for p in sorted((ROOT / folder).glob('*.md'))]
    result = {}
    for path in inputs:
        meta, body = parse(path)
        if vault and meta.get('publish', '').lower() != 'true':
            continue
        slug = meta.get('slug', path.stem)
        source = ('essays' if slug == 'stanford-essays' else 'notebook') if vault else path.parent.name
        branch = meta.get('branch', 'Writing' if source == 'essays' else '')
        title = meta.get('title', path.stem)
        kind = meta.get('kind', 'Essay' if branch == 'Writing' else 'Note')
        date = meta.get('date', '')
        if not SLUG.fullmatch(slug) or branch not in BRANCHES or slug in result:
            raise ValueError(f'{path.name}: use a unique lowercase hyphenated slug and a listed branch.')
        if date and not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])(-\d{2})?', date):
            raise ValueError(f'{path.name}: use YYYY-MM or YYYY-MM-DD for the date.')
        # Obsidian comments are author-only, even inside a published note.
        if body.count('%%') % 2:
            raise ValueError(f'{path.name}: close the %% comment before publishing.')
        body = re.sub(r'%%.*?%%', '', body, flags=re.S).strip()
        filename = path.stem if vault else meta.get('filename', path.stem)
        result[slug] = Note(slug, title, branch, kind, date, body, source, filename)
    return result


def link_map(notes):
    names = {}
    for note in notes.values():
        for key in (note.title, note.slug, note.filename):
            old = names.setdefault(key.casefold(), note)
            if old != note:
                raise ValueError(f'Two public notes use the name {key}.')
    return names


def wiki_parts(value):
    target, _, alias = value.partition('|')
    return target.strip(), alias.strip() or target.strip()


def inline(line, names, prefix='../'):
    parts = []
    end = 0
    for match in INLINE.finditer(line):
        parts.append(escape(line[end:match.start()]))
        tok = match[0]
        if tok.startswith('[['):
            key, label = wiki_parts(tok[2:-2])
            if key.casefold() not in names:
                raise ValueError(f'Link to unpublished or missing note: [[{key}]]. Remove the link or publish its target.')
            parts.append(f'<a href="{prefix}{names[key.casefold()].url}">{escape(label)}</a>')
        elif tok.startswith('['):
            label, url = tok[1:-1].split('](', 1)
            if urlsplit(url).scheme not in ('https', 'http', 'mailto'):
                raise ValueError(f'Use a public web address or a [[note link]] for {label}.')
            parts.append(f'<a href="{escape(url)}">{escape(label)}</a>')
        elif tok.startswith('**'):
            parts.append(f'<strong>{escape(tok[2:-2])}</strong>')
        else:
            tag = 'em' if tok.startswith('*') else 'code'
            parts.append(f'<{tag}>{escape(tok[1:-1])}</{tag}>')
        end = match.end()
    return ''.join(parts) + escape(line[end:])


def markdown(body, names):
    blocks = []
    for block in re.split(r'\n\s*\n', body.strip()):
        lines = block.splitlines()
        if not lines:
            continue
        if block == '---':
            blocks.append('<hr>')
        elif block.startswith('> '):
            blocks.append('<blockquote>' + inline('\n'.join(l.removeprefix('> ') for l in lines), names) + '</blockquote>')
        elif all(l.startswith(('- ', '* ')) for l in lines):
            blocks.append('<ul>' + ''.join('<li>' + inline(l[2:], names) + '</li>' for l in lines) + '</ul>')
        elif block.startswith('#'):
            heading = re.match(r'^#{1,6} (.+)$', lines[0])
            if heading:
                blocks.append(f'<h2>{inline(heading[1], names)}</h2>')
                if len(lines) > 1:
                    blocks.append('<p>' + inline('\n'.join(lines[1:]), names) + '</p>')
            else:
                blocks.append('<p>' + inline(block, names) + '</p>')
        else:
            blocks.append('<p>' + '<br>'.join(inline(l, names) for l in lines) + '</p>')
    return '\n'.join(blocks)


def template(name, **values):
    return Template((ROOT / 'layout' / name).read_text()).substitute(values)


def page(title, section, content, root='../', description='Notes and essays from Saanvi Mehra’s mango tree.'):
    paths = [('Tree', 'index.html'), ('Notebook', 'garden/index.html'),
             ('Connections', 'connections/index.html'), ('About', 'about/index.html')]
    links = []
    for label, path in paths:
        current = ' aria-current="page"' if section == label else ''
        links.append(f'<a{current} href="{root}{path}">{label}</a>')
    html = template('shell.html', title=escape(title), description=escape(description), root=root,
                    nav=''.join(links), main=content)
    return html.replace('<html', GENERATED + '\n<html', 1)


def note_link(note, root='../'):
    return f'<a href="{root}{note.url}">{escape(note.title)}</a>'


def rows(notes, root='../'):
    items = []
    for n in notes:
        meta = n.date_label or n.kind
        items.append(f'<li><a class="entry" href="{root}{n.url}"><span class="entry-meta">{escape(meta)}</span>'
                     f'<span class="entry-title">{escape(n.title)}</span><span class="entry-branch">'
                     f'<i class="seed {n.branch.lower()}"></i>{n.branch}</span></a></li>')
    return '<ul class="entries">' + ''.join(items) + '</ul>'


def sort_notes(notes):
    return sorted(sorted(notes, key=lambda n: n.title.casefold()), key=lambda n: n.date, reverse=True)


def build(notes):
    names = link_map(notes)
    outgoing = {}
    incoming = defaultdict(set)
    pages = {}
    for n in notes.values():
        related = {wiki_parts(m[1])[0].casefold() for m in WIKI.finditer(n.body)}
        outgoing[n.slug] = set()
        for key in related:
            if key not in names:
                raise ValueError(f'{n.title} links to an unpublished or missing note: [[{key}]].')
            target = names[key].slug
            if target != n.slug:
                outgoing[n.slug].add(target)
                incoming[target].add(n.slug)

    for n in notes.values():
        back = sort_notes(notes[s] for s in incoming[n.slug])
        backlinks = ''
        if back:
            backlinks = '<aside class="related"><h2>Linked from</h2><ul>' + ''.join(
                f'<li>{note_link(b)}</li>' for b in back) + '</ul></aside>'
        breadcrumb = f'<a href="../garden/{n.branch.lower()}.html">{n.branch}</a>'
        meta = ' · '.join(filter(None, [n.date_label, n.kind]))
        specimen = template('type-specimen.html') if n.slug == 'guthli' else ''
        content = (f'<article class="reader"><p class="folio">{breadcrumb} <span>/</span> {escape(meta)}</p>'
                   f'<h1>{escape(n.title)}</h1>{specimen}<div class="prose">{markdown(n.body, names)}</div>{backlinks}'
                   f'<a class="map-link" href="../connections/index.html#{n.slug}">See connections</a></article>')
        pages[n.url] = page(n.title + ' · Saanvi Mehra', 'Notebook', content)

    all_notes = sort_notes(notes.values())
    for branch in [None, *BRANCHES]:
        title = branch or 'The notebook'
        subtitle = BRANCHES[branch][0] if branch else 'Essays, reading notes, and things worth keeping.'
        filtered = [n for n in all_notes if not branch or n.branch == branch]
        chips = []
        for item in ['All', *BRANCHES]:
            path = 'index' if item == 'All' else item.lower()
            active = ' aria-current="page"' if item == (branch or 'All') else ''
            chips.append(f'<a href="{path}.html"{active}>{item}</a>')
        content = (f'<section class="listing"><h1>{title}</h1><p class="dek">{subtitle}</p>'
                   f'<nav class="chips" aria-label="Notebook shelves">{"".join(chips)}</nav>'
                   f'{rows(filtered) if filtered else "<p>No public notes on this shelf yet.</p>"}</section>')
        pages[f'garden/{branch.lower() if branch else "index"}.html'] = page(title + ' · Saanvi Mehra','Notebook', content)

    fruit = ''.join(f'<a class="fruit" href="garden/{b.lower()}.html" style="--x:{x}%;--y:{y}%" '
                    f'aria-label="{b} shelf"><span class="fruit-mark" aria-hidden="true">+</span>'
                    f'<span class="fruit-label">{b}</span></a>' for b, (_, x, y) in BRANCHES.items())
    cities = ''.join(f'<button type="button" aria-pressed="{str(i == 0).lower()}" data-zone="{zone}">{city}</button>'
                     for i, (city, zone) in enumerate([('Delhi','Asia/Kolkata'),('Philadelphia','America/New_York'),
                                                       ('San Francisco','America/Los_Angeles')]))
    picks = [notes[s] for s in ['stanford-essays','first-mango','lucky-13'] if s in notes]
    home = template('home.html', fruit=fruit, cities=cities, rows=rows(picks or all_notes[:3], ''))
    if 'first-mango' not in notes:
        home = home.replace('notes/first-mango.html', 'https://genius.com/John-agard-english-girl-eats-her-first-mango-annotated')
    pages['index.html'] = page('Saanvi Mehra · Under the mango tree', 'Tree', home, root='')
    about = template('about.html')
    for url in re.findall(r'href="\.\./(notes/[^"]+)"', about):
        if url not in pages:
            about = re.sub(r'<a href="\.\./' + re.escape(url) + r'">([^<]+)</a>', r'\1', about)
    pages['about/index.html'] = page('About · Saanvi Mehra', 'About', about)
    graph = [dict(slug=n.slug, title=n.title, branch=n.branch, kind=n.kind, url='../'+n.url,
                  neighbours=sorted(outgoing[n.slug] | incoming[n.slug])) for n in all_notes]
    graph_json = json.dumps(graph, ensure_ascii=False).replace('<', r'\u003c')
    graph_page = (f'<section class="network"><h1>Connections</h1><p class="dek">One note and its neighbours. '
                  f'Choose a title to follow the thread.</p><div id="graph"></div>'
                  f'<script type="application/json" id="graph-data">{graph_json}</script>'
                  f'<noscript>{rows(all_notes)}</noscript></section>')
    pages['connections/index.html'] = page('Connections · Saanvi Mehra', 'Connections', graph_page)
    return pages


def public_markdown(n):
    fields = dict(title=n.title, slug=n.slug, branch=n.branch, kind=n.kind)
    if n.filename not in (n.slug, n.title):
        fields['filename'] = n.filename
    if n.date:
        fields['date'] = n.date
    return '---\n' + ''.join(f'{k}: {json.dumps(v, ensure_ascii=False)}\n' for k, v in fields.items()) + '---\n\n' + n.body + '\n'


def save(notes, pages, importing):
    if importing:
        sources = {f'{n.source}/{n.slug}.md': public_markdown(n) for n in notes.values()}
        # Only these two folders are the public notebook source. A complete vault export
        # also withdraws notes that have moved to the desk or lost their publish flag.
        for folder in ('essays', 'notebook'):
            for old in (ROOT / folder).glob('*.md'):
                if old.relative_to(ROOT).as_posix() not in sources:
                    old.unlink()
        for path, text in sources.items():
            (ROOT / path).write_text(text)
    for folder in ('writing','notes'):
        for old in (ROOT / folder).glob('*.html'):
            if old.relative_to(ROOT).as_posix() not in pages and GENERATED in old.read_text()[:120]:
                old.unlink()
    for path, html in pages.items():
        out = ROOT / path
        out.parent.mkdir(exist_ok=True)
        out.write_text(html)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault', type=Path)
    parser.add_argument('--push', nargs='?', const='Update garden')
    args = parser.parse_args()
    try:
        public = read_notes(args.vault)
        rendered = build(public)
        save(public, rendered, args.vault is not None)
        print(f'Built {len(rendered)} pages from {len(public)} public notes.')
        if args.push is not None:
            subprocess.run([str(ROOT / 'publish'), args.push], cwd=ROOT, check=True)
    except (OSError, ValueError) as exc:
        parser.exit(1, str(exc) + '\n')
