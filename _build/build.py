#!/usr/bin/env python3
"""Builds the background pages of nordpflege24.de (guides, services, regions, jobs) from _build/content.

Run from anywhere:  python3 _build/build.py
Each file _build/content/<section>/<slug>.html becomes the page /<section>/<slug>/ on the website.
A content file starts with an HTML comment holding a JSON object (title, description, h1, lede, ...),
followed by the article body as plain HTML. The script adds navigation, footer, breadcrumb, FAQ,
sources, related pages, the structured data for search engines, the four overview pages and sitemap.xml.
The start page and the legal pages are written by hand and are not touched, except for sitemap.xml.
"""
import html
import json
import pathlib
import re
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / '_build' / 'content'
BASE = 'https://nordpflege24.de'
DEFAULT_DATE = '2026-10-05'
DEFAULT_STAND = 'Oktober 2026'
ORG_ID = BASE + '/#organisation'

SECTIONS = {
    'pflegedienst': {
        'name': 'Regionen',
        'title': 'Pflegedienst finden im Norden: alle Regionen | Nordpflege24',
        'description': 'Pflegedienst gesucht in Hamburg, Schleswig-Holstein oder Norddeutschland? Nordpflege24 vermittelt kostenlos einen Pflegedienst mit freier Kapazität in Ihrer Region.',
        'h1': 'Pflegedienst finden im Norden',
        'lede': 'Wir fragen für Sie bei Pflegediensten in Ihrer Region nach, wer freie Kapazität hat. Wählen Sie Ihren Ort oder fragen Sie direkt an.',
        'cta': 'pflege',
    },
    'leistungen': {
        'name': 'Leistungen',
        'title': 'Ambulante Pflege zu Hause: alle Leistungen | Nordpflege24',
        'description': 'Von Grundpflege bis Intensivpflege: Welche Leistungen ein ambulanter Pflegedienst zu Hause erbringt, wer sie bezahlt und wie Nordpflege24 kostenlos vermittelt.',
        'h1': 'Pflege zu Hause: unsere Leistungen im Überblick',
        'lede': 'Welche Hilfe ein ambulanter Pflegedienst leistet, wer die Kosten trägt und wie Sie über Nordpflege24 einen Dienst mit freier Kapazität finden.',
        'cta': 'pflege',
    },
    'ratgeber': {
        'name': 'Ratgeber',
        'title': 'Ratgeber Pflege: Pflegegrad, Kosten, Leistungen | Nordpflege24',
        'description': 'Verständliche Antworten rund um die Pflege zu Hause: Pflegegrad beantragen, Leistungen der Pflegekasse, Kosten, Entlastung für Angehörige. Stand 2026.',
        'h1': 'Ratgeber Pflege',
        'lede': 'Verständliche Antworten auf die Fragen, die sich stellen, wenn ein Mensch Pflege braucht. Mit den aktuellen Beträgen der Pflegekasse.',
        'cta': 'pflege',
    },
    'jobs': {
        'name': 'Jobs in der Pflege',
        'title': 'Jobs in der Pflege im Norden: Stellen und Gehalt | Nordpflege24',
        'description': 'Jobs für Pflegefachkräfte, Pflegehelfer und Quereinsteiger in Hamburg und Norddeutschland. Ohne Lebenslauf, diskret und kostenlos über Nordpflege24.',
        'h1': 'Jobs in der Pflege im Norden',
        'lede': 'Wir bringen dich mit Arbeitgebern in der Pflege zusammen, die zu dir passen. Ohne Lebenslauf, diskret und kostenlos.',
        'cta': 'job',
    },
}
SECTION_ORDER = ['pflegedienst', 'leistungen', 'ratgeber', 'jobs']

LOGO_SVG = ('<svg width="28" height="28" viewBox="0 0 48 48" aria-hidden="true"><path d="M8 21.5 24 8l16 13.5V40a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2Z" '
            'fill="none" stroke="currentColor" stroke-width="3.4" stroke-linejoin="round"/><path transform="translate(15.84 21.2) scale(.34)" '
            'd="M24 42C9 31 4 23.5 4 16 4 9.6 8.9 5 14.8 5c3.9 0 7.3 2 9.2 5.2C25.9 7 29.3 5 33.2 5 39.1 5 44 9.6 44 16c0 7.5-5 15-20 26Z" fill="currentColor"/></svg>')

NAV = '''<nav class="nav" aria-label="Hauptnavigation">
  <div class="wrap">
    <div class="nav-left">
      <details class="menu">
        <summary aria-label="Menü öffnen oder schließen"><svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><path d="M2.5 5h13M2.5 9h13M2.5 13h13" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg><span>Menü</span></summary>
        <div class="menu-panel">
          <a href="/">Startseite</a>
          <a href="/#start">Pflege finden</a>
          <a href="/#job">Jobs für Pflegekräfte</a>
          <a href="/#ueber-uns">Über uns</a>
          <hr>
          <a href="/impressum.html">Impressum</a>
          <a href="/datenschutz.html">Datenschutz</a>
        </div>
      </details>
      <a class="logo" href="/" aria-label="Nordpflege24, zur Startseite">
      ''' + LOGO_SVG + '''
      <span>Nordpflege<b>24</b></span>
    </a>
    </div>
    <a class="nav-call" href="https://wa.me/4915218903566" target="_blank" rel="noopener" aria-label="WhatsApp schreiben: 0152 18 90 35 66"><img src="/images/whatsapp.png" width="22" height="22" alt=""><span class="nav-num">WhatsApp</span></a>
  </div>
</nav>
'''

FOOTER = '''<footer class="foot">
  <div class="wrap">
    <div class="foot-grid">
      <div class="foot-brand">
        <a class="logo" href="/" aria-label="Nordpflege24, zur Startseite">
          ''' + LOGO_SVG + '''
          <span>Nordpflege<b>24</b></span>
        </a>
        <p>Kostenlose Vermittlung von Pflegediensten und Jobs in der Pflege. In Hamburg, Schleswig-Holstein und ganz Norddeutschland.</p>
      </div>
      <div class="foot-col">
        <h2>Kontakt</h2>
        <dl class="foot-contact">
          <div><dt>Telefon</dt><dd><a href="tel:+494065390431">040 65 39 04 31</a></dd></div>
          <div><dt>WhatsApp</dt><dd><a href="https://wa.me/4915218903566" target="_blank" rel="noopener">0152 18 90 35 66</a></dd></div>
          <div><dt>E-Mail</dt><dd><a href="mailto:kontakt@nordpflege24.de">kontakt@nordpflege24.de</a></dd></div>
        </dl>
        <p class="foot-note">Rückruf innerhalb von 24 Stunden.</p>
      </div>
      <nav class="foot-col" aria-label="Angebot">
        <h2>Angebot</h2>
        <ul>
          <li><a href="/#start">Pflege finden</a></li>
          <li><a href="/#job">Jobs für Pflegekräfte</a></li>
          <li><a href="/pflegedienst/">Regionen</a></li>
          <li><a href="/leistungen/">Leistungen</a></li>
          <li><a href="/ratgeber/">Ratgeber</a></li>
          <li><a href="/jobs/">Jobs in der Pflege</a></li>
        </ul>
      </nav>
      <div class="foot-col">
        <h2>Anbieter</h2>
        <address>RAIT Solution<br>Neuer Wall 1<br>20354 Hamburg</address>
        <ul>
          <li><a href="/impressum.html">Impressum</a></li>
          <li><a href="/datenschutz.html">Datenschutz</a></li>
          <li><a href="/agb.html">AGB</a></li>
        </ul>
      </div>
    </div>
    <div class="foot-bottom">
      <span>© 2026 Nordpflege24. Ein Angebot von RAIT Solution.</span>
      <span>Hamburg · Schleswig-Holstein · Norddeutschland</span>
    </div>
  </div>
</footer>

<a class="wa" href="https://wa.me/4915218903566" target="_blank" rel="noopener" aria-label="Per WhatsApp schreiben"><img src="/images/whatsapp.png" alt="" width="40" height="40"><span>WhatsApp</span></a>

<script src="/menu.js"></script>
</body>
</html>
'''

warnings = []


def warn(msg):
    warnings.append(msg)


def esc(text):
    return html.escape(str(text), quote=True)


def plain(text):
    """Text without tags, for structured data."""
    return html.unescape(re.sub(r'<[^>]+>', '', str(text))).strip()


def ld(data):
    return '  <script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '</script>\n'


def read_page(path):
    raw = path.read_text(encoding='utf-8')
    m = re.match(r'\s*<!--\s*(\{.*?\})\s*-->', raw, flags=re.S)
    if not m:
        sys.exit(f'{path}: the file must start with <!-- {{ ... }} -->')
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        sys.exit(f'{path}: the JSON at the top is not valid ({e})')
    section = path.parent.name
    slug = path.stem
    for key in ('title', 'description', 'h1', 'lede'):
        if not meta.get(key):
            sys.exit(f'{path}: "{key}" is missing')
    meta.update(section=section, slug=slug, key=f'{section}/{slug}', url=f'/{section}/{slug}/', body=raw[m.end():].strip())
    meta.setdefault('cta', SECTIONS[section]['cta'])
    meta.setdefault('stand', DEFAULT_STAND)
    meta.setdefault('datum', DEFAULT_DATE)
    meta.setdefault('kurz', meta['description'])
    return meta


def cta_block(meta):
    if meta['cta'] == 'job':
        return '<a class="btn" href="/#job">Job finden</a><span>Ohne Lebenslauf. Diskret und kostenlos.</span>'
    href = '/#start'
    if meta.get('ort'):
        href = '/?ort=' + urllib.parse.quote(meta['ort']) + '#start'
    return f'<a class="btn" href="{href}">Pflege anfragen</a><span>Kostenlos. Rückruf innerhalb von 24 Stunden.</span>'


def closing_band(meta):
    if meta['cta'] == 'job':
        return ('<h2>Bereit für einen Job, der zu dir passt?</h2><p>Drei kurze Fragen, deine Telefonnummer, fertig. Wir melden uns innerhalb von 24 Stunden.</p>'
                '<a class="btn btn-light" href="/#job">Job finden</a>')
    href = '/#start'
    where = 'in Ihrer Nähe'
    if meta.get('ort'):
        href = '/?ort=' + urllib.parse.quote(meta['ort']) + '#start'
        where = 'in ' + esc(meta['ort'])
    return (f'<h2>Pflege {where} gesucht?</h2><p>Sagen Sie uns in 30 Sekunden, was gebraucht wird. Wir fragen bei den Pflegediensten nach und rufen innerhalb von 24 Stunden zurück.</p>'
            f'<a class="btn btn-light" href="{href}">Pflege anfragen</a>')


def head(title, description, url, robots='index, follow, max-image-preview:large', extra=''):
    return f'''<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="{robots}">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <link rel="canonical" href="{BASE}{url}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Nordpflege24">
  <meta property="og:title" content="{esc(title.split(' | ')[0])}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{BASE}{url}">
  <meta property="og:locale" content="de_DE">
  <meta property="og:image" content="{BASE}/images/hero.jpg">
  <meta name="twitter:card" content="summary_large_image">
{extra}  <link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/styles.css">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <meta name="theme-color" content="#0E5A63">
</head>
<body>

'''


def crumbs_html(trail):
    parts = []
    for i, (name, url) in enumerate(trail):
        if i == len(trail) - 1:
            parts.append(f'<span aria-current="page">{esc(name)}</span>')
        else:
            parts.append(f'<a href="{url}">{esc(name)}</a><span aria-hidden="true">›</span>')
    return '<nav class="crumbs" aria-label="Sie sind hier">' + ''.join(parts) + '</nav>'


def crumbs_ld(trail):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': name, 'item': BASE + url} for i, (name, url) in enumerate(trail)]}


def tile(page):
    return (f'<a class="tile tile-link" href="{page["url"]}"><h3>{esc(page.get("karte") or page["h1"])}</h3>'
            f'<p>{esc(page["kurz"])}</p></a>')


def render_page(meta, pages):
    sec = SECTIONS[meta['section']]
    trail = [('Startseite', '/'), (sec['name'], f'/{meta["section"]}/'), (meta.get('krume') or meta['h1'], meta['url'])]

    extra = ld(crumbs_ld(trail))
    org = {'@type': 'Organization', '@id': ORG_ID, 'name': 'Nordpflege24', 'url': BASE + '/'}
    if meta['section'] == 'ratgeber':
        extra += ld({'@context': 'https://schema.org', '@type': 'Article', 'headline': meta['h1'], 'description': meta['description'],
                     'inLanguage': 'de', 'datePublished': meta.get('erstellt', meta['datum']), 'dateModified': meta['datum'],
                     'author': org, 'publisher': org, 'image': BASE + '/images/hero.jpg', 'mainEntityOfPage': BASE + meta['url']})
    elif meta['section'] in ('leistungen', 'pflegedienst'):
        service = {'@context': 'https://schema.org', '@type': 'Service', 'name': meta['h1'], 'description': meta['description'],
                   'serviceType': meta.get('leistung', 'Vermittlung ambulanter Pflegedienste'), 'provider': org, 'url': BASE + meta['url'],
                   'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'EUR', 'description': 'Die Vermittlung ist kostenlos.'}}
        service['areaServed'] = meta.get('ort') or ['Hamburg', 'Schleswig-Holstein', 'Norddeutschland']
        extra += ld(service)
    faq = meta.get('faq') or []
    if faq:
        extra += ld({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': plain(f['q']), 'acceptedAnswer': {'@type': 'Answer', 'text': plain(f['a'])}} for f in faq]})

    out = head(meta['title'], meta['description'], meta['url'], extra=extra) + NAV
    out += '\n<main>\n  <div class="wrap">\n    ' + crumbs_html(trail) + '\n'
    out += f'''    <header class="page-hero">
      <p class="eyebrow">{esc(meta.get('eyebrow') or sec['name'])}</p>
      <h1>{esc(meta['h1'])}</h1>
      <p class="lede">{esc(meta['lede'])}</p>
      <div class="page-cta">{cta_block(meta)}</div>
    </header>
    <article class="prose">
{meta['body']}
    </article>
'''
    if faq:
        out += '    <section class="page-block" aria-labelledby="fragen-h">\n      <h2 id="fragen-h">Häufige Fragen</h2>\n      <div class="faq">\n'
        for f in faq:
            out += f'        <details><summary>{esc(f["q"])}</summary><p>{f["a"]}</p></details>\n'
        out += '      </div>\n    </section>\n'

    quellen = meta.get('quellen') or []
    out += '    <aside class="sources">\n      <h2>Stand und Quellen</h2>\n'
    note = f'Stand: {esc(meta["stand"])}. Diese Seite informiert allgemein und ersetzt keine Beratung im Einzelfall, etwa durch Ihre Pflegekasse oder einen Pflegestützpunkt.'
    if meta['section'] == 'jobs':
        note = f'Stand: {esc(meta["stand"])}. Die Angaben sind allgemeine Informationen und kein verbindliches Angebot eines Arbeitgebers.'
    out += f'      <p>{note}</p>\n'
    if quellen:
        out += '      <ul>\n' + ''.join(
            f'        <li><a href="{esc(q["url"])}" target="_blank" rel="noopener">{esc(q["name"])}</a></li>\n' for q in quellen) + '      </ul>\n'
    out += '    </aside>\n'

    related = []
    for key in meta.get('related') or []:
        if key in pages and key != meta['key']:
            related.append(pages[key])
        elif key not in pages:
            warn(f'{meta["key"]}: related page "{key}" does not exist')
    if len(related) < 3:
        for p in pages.values():
            if p['section'] == meta['section'] and p['key'] != meta['key'] and p not in related:
                related.append(p)
            if len(related) >= 3:
                break
    if related:
        out += '    <section class="page-wide" aria-labelledby="weiter-h">\n      <h2 id="weiter-h">Weiterlesen</h2>\n      <div class="tiles">\n'
        out += ''.join('        ' + tile(p) + '\n' for p in related[:6])
        out += '      </div>\n    </section>\n'
    out += '  </div>\n\n  <section class="section section-tight">\n    <div class="wrap">\n      <div class="wide wide-dark">\n        <div class="wide-text">'
    out += closing_band(meta) + '</div>\n      </div>\n    </div>\n  </section>\n</main>\n\n' + FOOTER
    return out


def render_hub(section, pages):
    sec = SECTIONS[section]
    url = f'/{section}/'
    trail = [('Startseite', '/'), (sec['name'], url)]
    mine = [p for p in pages.values() if p['section'] == section]
    mine.sort(key=lambda p: (p.get('rang', 500), p['h1']))
    extra = ld(crumbs_ld(trail)) + ld({'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': sec['h1'], 'description': sec['description'],
                                       'url': BASE + url, 'inLanguage': 'de', 'hasPart': [{'@type': 'WebPage', 'name': p['h1'], 'url': BASE + p['url']} for p in mine]})
    out = head(sec['title'], sec['description'], url, extra=extra) + NAV
    out += '\n<main>\n  <div class="wrap">\n    ' + crumbs_html(trail) + '\n'
    out += f'''    <header class="page-hero">
      <p class="eyebrow">Nordpflege24</p>
      <h1>{esc(sec['h1'])}</h1>
      <p class="lede">{esc(sec['lede'])}</p>
      <div class="page-cta">{cta_block({'cta': sec['cta']})}</div>
    </header>
'''
    groups = []
    for p in mine:
        g = p.get('gruppe', '')
        if g not in groups:
            groups.append(g)
    for g in groups:
        out += '    <section class="page-wide">\n'
        if g:
            out += f'      <h2>{esc(g)}</h2>\n'
        out += '      <div class="tiles">\n' + ''.join('        ' + tile(p) + '\n' for p in mine if p.get('gruppe', '') == g) + '      </div>\n    </section>\n'
    others = [s for s in SECTION_ORDER if s != section]
    out += '    <section class="page-wide">\n      <h2>Mehr von Nordpflege24</h2>\n      <div class="tiles">\n'
    for s in others:
        out += f'        <a class="tile tile-link" href="/{s}/"><h3>{esc(SECTIONS[s]["name"])}</h3><p>{esc(SECTIONS[s]["lede"])}</p></a>\n'
    out += '      </div>\n    </section>\n  </div>\n\n  <section class="section section-tight">\n    <div class="wrap">\n      <div class="wide wide-dark">\n        <div class="wide-text">'
    out += closing_band({'cta': sec['cta']}) + '</div>\n      </div>\n    </div>\n  </section>\n</main>\n\n' + FOOTER
    return out


def check(pages):
    titles, descs = {}, {}
    known = {p['url'] for p in pages.values()} | {f'/{s}/' for s in SECTIONS} | {'/', '/impressum.html', '/datenschutz.html', '/agb.html'}
    for p in pages.values():
        if len(p['title']) > 65:
            warn(f'{p["key"]}: title has {len(p["title"])} characters (max. 65)')
        if not 110 <= len(p['description']) <= 160:
            warn(f'{p["key"]}: description has {len(p["description"])} characters (110 to 160)')
        if p['title'] in titles:
            warn(f'{p["key"]}: same title as {titles[p["title"]]}')
        if p['description'] in descs:
            warn(f'{p["key"]}: same description as {descs[p["description"]]}')
        titles[p['title']] = p['key']
        descs[p['description']] = p['key']
        if '<h1' in p['body']:
            warn(f'{p["key"]}: the body must not contain an h1')
        words = len(re.sub(r'<[^>]+>', ' ', p['body']).split())
        if words < 450:
            warn(f'{p["key"]}: only {words} words in the body')
        for href in re.findall(r'href="([^"]+)"', p['body'] + ' '.join(f['a'] for f in p.get('faq') or [])):
            if href.startswith(('http://', 'https://', 'tel:', 'mailto:')):
                continue
            target = href.split('#')[0].split('?')[0]
            if target not in known:
                warn(f'{p["key"]}: link to "{href}" has no target')
        if '—' in p['body'] or '–' in p['lede']:
            warn(f'{p["key"]}: please no long dashes')


def main():
    pages = {}
    for path in sorted(SRC.glob('*/*.html')):
        if path.parent.name not in SECTIONS:
            sys.exit(f'{path}: unknown section')
        meta = read_page(path)
        pages[meta['key']] = meta
    check(pages)
    for meta in pages.values():
        target = ROOT / meta['section'] / meta['slug'] / 'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_page(meta, pages), encoding='utf-8')
    for section in SECTIONS:
        if any(p['section'] == section for p in pages.values()):
            target = ROOT / section / 'index.html'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render_hub(section, pages), encoding='utf-8')
    urls = [('/', DEFAULT_DATE)]
    for section in SECTION_ORDER:
        mine = [p for p in pages.values() if p['section'] == section]
        if mine:
            urls.append((f'/{section}/', max(p['datum'] for p in mine)))
            urls += [(p['url'], p['datum']) for p in sorted(mine, key=lambda p: p['slug'])]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += ''.join(f'  <url><loc>{BASE}{u}</loc><lastmod>{d}</lastmod></url>\n' for u, d in urls) + '</urlset>\n'
    (ROOT / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
    print(f'{len(pages)} pages, {len(urls)} addresses in sitemap.xml')
    for w in warnings:
        print('WARNING', w)


if __name__ == '__main__':
    main()
