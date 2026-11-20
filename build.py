#!/usr/bin/env python3
"""Render the garden. An optional Obsidian vault supplies explicitly published notes."""
import argparse
import calendar
import json
import re
import subprocess
import unicodedata
from dataclasses import dataclass
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
# Each cultivar has an attachment point in the ink drawing. The editor can
# hang any published piece there without assigning it a subject.
FRUIT = [
    ('Alphonso', 'stanford-essays', 19.58333, 61.78571),
    ('Langra', 'lucky-13', 16.38889, 46.78571),
    ('Safeda', 'guthli', 84.72222, 32.32143),
]
COLLECTIONS = ('Found', 'Made')
VERSE = ('I see my life extending before me', 'like a mango tree,',
         'and I plan to make the most Frooti out of it.')
BYLINE = ('- Sylvia Plath', '(adapted by Saanvi Mehra)')
WIKI = re.compile(r'\[\[([^\]\n]+)\]\]')
INLINE = re.compile(r'\[\[[^\]\n]+\]\]|\[[^\]\n]+\]\([^\s)]+\)|\*\*[^*\n]+\*\*|\*[^*\n]+\*|`[^`\n]+`')
GENERATED = '<!-- Built by the mango notebook. -->'
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')


@dataclass
class Note:
    slug: str
    title: str
    kind: str
    date: str
    body: str
    source: str
    filename: str
    collections: tuple
    glimpse: str

    @property
    def passages(self):
        """Separate an optional closing list of authored connections from the text."""
        return re.split(r'^## Connections[ \t]*$', self.body, maxsplit=1, flags=re.M)

    @property
    def url(self):
        return 'index.html#about-me' if self.slug == 'saanvi-mehra' else self.source_page

    @property
    def source_page(self):
        if self.slug == 'saanvi-mehra':
            return 'about/index.html'
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
        title = meta.get('title', path.stem)
        kind = meta.get('kind', 'Essay' if source == 'essays' else 'Note')
        date = meta.get('date', '')
        if not SLUG.fullmatch(slug) or slug in result:
            raise ValueError(f'{path.name}: use a unique lowercase hyphenated slug.')
        if date and not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])(-\d{2})?', date):
            raise ValueError(f'{path.name}: use YYYY-MM or YYYY-MM-DD for the date.')
        # Obsidian comments are author-only, even inside a published note.
        if body.count('%%') % 2:
            raise ValueError(f'{path.name}: close the %% comment before publishing.')
        body = re.sub(r'%%.*?%%', '', body, flags=re.S).strip()
        filename = path.stem if vault else meta.get('filename', path.stem)
        legacy = {'Upstream': 'Found', 'Commits': 'Made'}.get(meta.get('stream'), '')
        collections = tuple(s.strip() for s in meta.get('collection', legacy).split(',') if s.strip())
        if set(collections).difference(COLLECTIONS):
            raise ValueError(f'{path.name}: collection accepts Found, Made, or both separated by a comma.')
        result[slug] = Note(slug, title, kind, date, body, source, filename, collections, meta.get('glimpse', ''))
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


def inline(line, names, root=''):
    parts = []
    end = 0
    for match in INLINE.finditer(line):
        parts.append(escape(line[end:match.start()]))
        tok = match[0]
        if tok.startswith('[['):
            key, label = wiki_parts(tok[2:-2])
            if key.casefold() not in names:
                raise ValueError(f'Link to unpublished or missing note: [[{key}]]. Remove the link or publish its target.')
            parts.append(f'<a href="{root}{names[key.casefold()].url}">{escape(label)}</a>')
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


def markdown(body, names, root=''):
    blocks = []
    for block in re.split(r'\n\s*\n', body.strip()):
        lines = block.splitlines()
        if not lines:
            continue
        if block == '---':
            blocks.append('<hr>')
        elif block.startswith('> '):
            blocks.append('<blockquote>' + inline('\n'.join(l.removeprefix('> ') for l in lines), names, root) + '</blockquote>')
        elif all(l.startswith(('- ', '* ')) for l in lines):
            blocks.append('<ul>' + ''.join('<li>' + inline(l[2:], names, root) + '</li>' for l in lines) + '</ul>')
        elif block.startswith('#'):
            heading = re.match(r'^#{1,6} (.+)$', lines[0])
            if heading:
                blocks.append(f'<h2>{inline(heading[1], names, root)}</h2>')
                if len(lines) > 1:
                    blocks.append('<p>' + inline('\n'.join(lines[1:]), names, root) + '</p>')
            else:
                blocks.append('<p>' + inline(block, names, root) + '</p>')
        else:
            blocks.append('<p>' + '<br>'.join(inline(l, names, root) for l in lines) + '</p>')
    return '\n'.join(blocks)


def template(name, **values):
    return Template((ROOT / 'layout' / name).read_text()).substitute(values)


def character_sheet(*, afterword):
    groups = {key: [] for key in ('Uppercase', 'Lowercase', 'Numbers', 'Extended Latin',
                                  'Punctuation and symbols', 'Combining marks', 'Spaces and controls')}
    for span in (ROOT / 'layout/guthli-codepoints.txt').read_text().split():
        low, _, high = span.partition('-')
        for code in range(int(low, 16), int(high or low, 16) + 1):
            char = chr(code)
            name = unicodedata.name(char)
            category = unicodedata.category(char)[0]
            if 'A' <= char <= 'Z':
                group = 'Uppercase'
            elif 'a' <= char <= 'z':
                group = 'Lowercase'
            elif category == 'N':
                group = 'Numbers'
            elif name.startswith('LATIN '):
                group = 'Extended Latin'
            elif category == 'M':
                group = 'Combining marks'
            elif category in ('C', 'Z'):
                group = 'Spaces and controls'
            else:
                group = 'Punctuation and symbols'
            label = escape(name.lower())
            if group == 'Spaces and controls':
                sample = f'<span class="space-name">{label}</span>'
            else:
                sample = f'<span class="drawn-char">{escape(("x" if category == "M" else "") + char)}</span>'
            groups[group].append(f'<li data-code="{code:04X}" title="{label} · U+{code:04X}" '
                                 f'aria-label="{label}, U+{code:04X}">{sample}<small>U+{code:04X}</small></li>')
    sections = []
    for title, cells in groups.items():
        hint = '<p>Each mark is shown on x.</p>' if title == 'Combining marks' else ''
        css = 'char-grid spaces' if title == 'Spaces and controls' else 'char-grid'
        section_id = title.lower().replace(' ', '-')
        sections.append(f'<section id="{section_id}"><h2>{title} <small>{len(cells)}</small></h2>{hint}'
                        f'<ul class="{css}">' + ''.join(cells) + '</ul></section>')
    return template('characters.html', afterword=afterword,
                    count=sum(map(len, groups.values())), sections=''.join(sections))


def sort_notes(notes):
    return sorted(sorted(notes, key=lambda n: n.title.casefold()), key=lambda n: n.date, reverse=True)


def profile_html(note, names):
    if not note:
        return ''
    # Each titled section starts with the short reading, followed by the full passage.
    preface, *sections = re.split(r'^### (.+)$', note.passages[0], flags=re.M)
    items = []
    venn = template('venn.html')
    for paragraph in re.split(r'\n\s*\n', preface.strip()):
        if paragraph:
            items.append('<li>' + profile_copy(paragraph, names, f'intro-{len(items)}') + '</li>')
    for index in range(0, len(sections), 2):
        label, body = sections[index:index + 2]
        readings = re.split(r'\n\s*\n', body.strip(), maxsplit=1)
        brief = profile_copy(readings[0], names, f'brief-{index}')
        if len(readings) == 1:
            items.append(f'<li>{brief}</li>')
            continue
        full = profile_copy(readings[1], names, f'full-{index}')
        items.append(f'<li><details class="bio-fold"><summary title="Expand or collapse this paragraph">'
                     f'{venn}<span class="sr">{escape(label)}</span>'
                     f'</summary><div class="bio-full">{full}</div></details>'
                     f'<div class="bio-brief">{brief}</div></li>')
    return '<ul class="bio-list" role="list">' + ''.join(items) + '</ul>'


def profile_copy(passage, names, reading):
    html = markdown(passage, names)
    glosses = {'धर्म': 'Dharma — In Hinduism, dharma signifies behaviours considered to be in accord with the order that makes life and the universe possible — duty, law, ethics, and right action.', 'कर्म': 'Karma — In Indian religions, karma is the concept of action, work, or deed and its effect on the future of an individual — the spiritual principle of cause and effect.', 'Advaita Vedantic': 'Advaita Vedanta — A Hindu non-dual philosophy meaning "not two". It teaches that the individual soul (Atman) and the ultimate absolute reality (Brahman) are identical.'}
    for label, gloss in glosses.items():
        title, definition = gloss.split(' — ', 1)
        key = title.lower().replace(' ', '-') + '-' + reading
        def card(match):
            url = match[1]
            native = f'<span class="gloss-script" lang="sa">{label}</span>' if label != 'Advaita Vedantic' else ''
            return (f'<span class="gloss"><a class="gloss-link" href="{url}" title="{escape(gloss)}">{label}</a>'
                    f'<span class="gloss-card" id="gloss-{key}" role="group" aria-label="{title}" hidden>'
                    f'<span class="gloss-heading">{native}<strong>{title}</strong></span>'
                    f'<span class="gloss-definition">{escape(definition)}</span>'
                    f'<a href="{url}">Read more about {title} ↗</a></span></span>')
        html = re.sub(r'<a href="([^"]+)">' + re.escape(label) + r'</a>', card, html)
    return html.replace('My favourite colour is green.', '<span class="favourite-green">My favourite colour is green.</span>')


def collection_contents(label, entries):
    rows = []
    for note in entries:
        if label in (note.collections or ('Made',)):
            rows.append(f'<li><a class="entry-link" data-slug="{note.slug}" href="{note.url}">'
                        f'<span class="entry-title">{escape(note.title)}</span> '
                        f'<span class="entry-meta">{escape(note.date_label)}</span></a></li>')
    return ('<ul class="entry-list" role="list">' + ''.join(rows) + '</ul>'
            if rows else '<p class="coming-soon">Coming soon.</p>')


def piece_page(note, names, credits):
    collection = (note.collections or ('Made',))[0]
    title = escape(note.title)
    body = markdown(note.passages[0], names, '../')
    extras = ''
    article_class = 'reading-page'
    if note.slug == 'guthli':
        article_class += ' specimen'
        extras = '<link rel="stylesheet" href="../assets/character-sheet.css?v=folio2">'
        body = character_sheet(afterword=f'<div class="type-story prose">{body}</div>')
    else:
        body = f'<div class="prose">{body}</div>'
    date = f'<p class="folio">{escape(note.date_label)}</p>' if note.date_label else ''
    main = (f'<article class="{article_class}"><header>'
            f'<a class="back-link" href="../index.html#{collection.lower()}">← {collection}</a>'
            f'<h1>{title}</h1>{date}</header>{body}</article>')
    return template('shell.html', title=f'{title} · Saanvi Mehra', description=title, wordmark=template('wordmark.html').strip(),
                    page_class='piece-page', root='../', credits=credits, extras=extras, page_path=note.url, page_type='article',
                    alternate=note.slug+'.html.md', main=main, skip_target='#main', skip_text='Skip to piece')


def redirect(dest, aliases=()):
    forward = ''
    if aliases:
        forward = ('<script>const ids=' + json.dumps(aliases) + ';const id=location.hash.slice(1);'
                   'if(Object.hasOwn(ids,id)) location.replace(ids[id]);</script>')
    return ('<!doctype html>\n' + GENERATED + '\n<html lang="en"><head><meta charset="utf-8">'
            '<title>Saanvi Mehra</title>' + forward + f'<meta http-equiv="refresh" content="0; url={dest}">'
            f'</head><body><a href="{dest}">Continue to Saanvi’s website</a></body></html>\n')


def build(notes):
    names = link_map(notes)
    entries = sort_notes(n for n in notes.values() if n.slug != 'saanvi-mehra')
    fruit = []
    for cultivar, slug, x, y in FRUIT:
        if slug not in notes:
            continue
        n = notes[slug]
        stem = cultivar.lower()
        fruit.append(f'<a class="hanging-fruit" id="pick-{slug}" href="{n.url}" data-stem="{stem}" '
                     f'style="--x:{x}%;--y:{y}%"><img src="assets/fruit/{stem}.webp" alt="" width="88" height="104">'
                     f'<span class="fruit-label">{escape(n.title)}<small>{cultivar}</small></span></a>')
    credits = template('credits.html')
    wordmark = template('wordmark.html').strip()
    home = template('home.html', wordmark=wordmark, outer_arc=VERSE[0], inner_arc=VERSE[1], verse_end=VERSE[2], author=BYLINE[0], adaptation=BYLINE[1],
                    fruit=''.join(fruit), profile=profile_html(notes.get('saanvi-mehra'), names),
                    made=collection_contents('Made', entries), found=collection_contents('Found', entries))
    pages = {'index.html': template('shell.html', title='Saanvi Mehra', wordmark=wordmark,
                                    description='Saanvi Mehra’s writing and projects, under a mango tree.',
                                    root='', alternate='llms.txt', page_class='tree-home', main=home, credits=credits, page_path='', page_type='website',
                                    extras='',
                                    skip_target='#made', skip_text='Skip to writing and projects')}
    pages.update({n.url: piece_page(n, names, credits) for n in entries})
    pages.update(agent_pages(notes, entries, names))

    old_paths = {'garden/index.html':'made', 'connections/index.html':'made', 'about/index.html':'about-me',
                 'notes/seventies-california.html':'found'}
    for folder, anchor in [('reading','found'), ('music','found'), ('writing','made'),
                           ('work','made'), ('hinduism','about-me'), ('roots','about-me')]:
        old_paths[f'garden/{folder}.html'] = anchor
    for slug in ('dharma-and-karma','noida','payments','intersection-sets','reading-and-translating'):
        old_paths[f'notes/{slug}.html'] = 'about-me'
    for path, anchor in old_paths.items():
        aliases = {}
        if path == 'about/index.html':
            aliases = dict.fromkeys(('photographs', 'sound'), '../index.html#credits')
        elif path == 'garden/index.html':
            aliases = {key: '../index.html#' + key for key in ('found','made')}
        pages.setdefault(path, redirect('../index.html#' + anchor, aliases))
    specimen = '../notes/guthli.html' if 'guthli' in notes else '../index.html#made'
    sections = ('uppercase','lowercase','numbers','extended-latin','punctuation-and-symbols',
                'combining-marks','spaces-and-controls','workshop')
    pages['type/characters.html'] = redirect(specimen, {key: specimen + '#' + key for key in sections} if 'guthli' in notes else {})
    return pages


def agent_pages(notes, entries, names):
    pages = {}
    def authored_text(note, root):
        def md_link(match):
            key, label = wiki_parts(match[1])
            return f'[{label}]({root}{names[key.casefold()].source_page}.md)'
        text = WIKI.sub(md_link, note.passages[0].strip())
        if note.slug == 'guthli':
            text += f'\n\n[Character sheet]({root}{note.url}#workshop) · [Download Guthli 1.0]({root}assets/Guthli-1.0.zip)'
        return text

    for note in notes.values():
        content = ['# ' + note.title, ' · '.join(filter(None, [note.kind, note.date_label])), authored_text(note, '../')]
        pages[note.source_page+'.md'] = '\n\n'.join(content) + '\n\n' + GENERATED + '\n'

    index = ['# Saanvi Mehra']
    if 'saanvi-mehra' in notes:
        index.extend(['## About me', authored_text(notes['saanvi-mehra'], '')])
    for label in ('Made', 'Found'):
        index.append('## ' + label)
        members = [n for n in entries if label in (n.collections or ('Made',))]
        index.append('\n'.join(f'- [{n.title}]({n.url}) · [Markdown]({n.source_page}.md)' for n in members) or 'Coming soon.')
    for note in entries:
        index.extend(['## ' + note.title, authored_text(note, '')])
    index.extend(['## Mango squeeze', '> ' + ' '.join(VERSE), ' '.join(BYLINE)])
    pages['llms.txt'] = '\n\n'.join(index) + '\n'
    return pages


def public_markdown(n):
    fields = dict(title=n.title, slug=n.slug, kind=n.kind)
    if n.filename not in (n.slug, n.title):
        fields['filename'] = n.filename
    if n.collections:
        fields['collection'] = ', '.join(n.collections)
    if n.glimpse:
        fields['glimpse'] = n.glimpse
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
    for folder in ('writing','notes','type'):
        for old in (ROOT / folder).glob('*.html'):
            if old.relative_to(ROOT).as_posix() not in pages and GENERATED in old.read_text()[:120]:
                old.unlink()
    for folder in ('writing', 'notes', 'about'):
        for old in (ROOT / folder).glob('*.html.md'):
            if old.relative_to(ROOT).as_posix() not in pages and old.read_text().rstrip().endswith(GENERATED):
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
        print(f'Built {len(rendered)} public files from {len(public)} notes.')
        if args.push is not None:
            subprocess.run([str(ROOT / 'publish'), args.push], cwd=ROOT, check=True)
    except (OSError, ValueError) as exc:
        parser.exit(1, str(exc) + '\n')
