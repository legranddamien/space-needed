#!/usr/bin/env python3
"""Render complete localized Pages documents using only Python's standard library."""
import argparse
from html import escape
import json
from pathlib import Path
import re
import string
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://legranddamien.github.io/space-needed/'
BASE = '/space-needed/'
LOCALES = {'en': 'English', 'fr-FR': 'Français', 'de': 'Deutsch', 'es': 'Español', 'it': 'Italiano', 'ja': '日本語', 'ko': '한국어', 'pt-BR': 'Português (Brasil)', 'zh-Hans': '简体中文'}
OG_LOCALES = dict(zip(LOCALES, ['en_US', 'fr_FR', 'de_DE', 'es_ES', 'it_IT', 'ja_JP', 'ko_KR', 'pt_BR', 'zh_CN']))
SCENES = ['onboarding', 'derived-data', 'docker', 'cleanup-review']
GROUPS = [(0, 7), (7, 9), (9, 13), (13, 16), (16, 18), (18, 21)]
SOURCE_IDS = ['xcode.derivedData', 'xcode.archives', 'xcode.deviceSupport', 'xcode.documentation', 'xcode.logs', 'simulators.devices', 'simulators.runtimes', 'developer.buildFolders', 'caches.packages', 'android.gradleCaches', 'android.gradleDistributions', 'android.projectBuilds', 'android.studioLogs', 'containers.docker', 'containers.docker', 'containers.tart', 'tools.cleanup', 'tools.cleanup', 'system.temp', 'caches.packages', 'system.localizations']
SPARKLE = '{http://www.andymatuschak.org/xml-namespaces/sparkle}'
GENERATED = ['index.html'] + [f'{locale}/index.html' for locale in LOCALES if locale != 'en'] + ['sitemap.xml', '404.html']


def locale_path(locale):
    """Keep English at the project root and give every translation a stable URL."""
    return '' if locale == 'en' else locale + '/'


def release_info(feed):
    """Read the highest published build, accepting only this project's immutable DMG URLs."""
    root = ET.parse(feed).getroot()
    releases = []
    for item in root.findall('./channel/item'):
        version = item.findtext(SPARKLE + 'shortVersionString', '')
        build = item.findtext(SPARKLE + 'version', '')
        enclosure = item.find('enclosure')
        if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version) or not build.isdigit() or int(build) < 1 or enclosure is None:
            raise ValueError('Invalid release metadata')
        expected = f'https://github.com/legranddamien/space-needed/releases/download/v{version}/SpaceNeeded.dmg'
        if enclosure.get('url') != expected:
            raise ValueError('Unexpected download URL')
        releases.append((int(build), version, expected))
    return max(releases) if releases else None


def validate_content(content):
    """Reject partial translations and malformed structured content instead of falling back silently."""
    if set(content) != set(LOCALES):
        raise ValueError('The website must contain all nine supported locales')
    def shape(value):
        if isinstance(value, dict):
            return {key: shape(item) for key, item in value.items()}
        if isinstance(value, list):
            return [shape(item) for item in value]
        if not isinstance(value, str) or not value.strip():
            raise ValueError('Empty or non-string translation')
        return 'text'
    expected = shape(content['en'])
    for locale, copy in content.items():
        if shape(copy) != expected or len(copy['sources']) != len(SOURCE_IDS) or len(copy['shots']) != 4 or len(copy['groups']) != 6 or len(copy['sourceNotes']) != 6:
            raise ValueError(f'Incomplete translation: {locale}')


def icon(size, class_name=''):
    """Use the approved native artwork with theme-aware selection and no decorative rotation."""
    return f'<picture class="app-icon {class_name}"><source data-dark srcset="{BASE}assets/brand/icon-dark.png" media="(prefers-color-scheme: dark)"><img src="{BASE}assets/brand/icon-light.png" width="{size}" height="{size}" alt="" decoding="async"></picture>'


def picture(scene, alt, eager=False):
    """Keep screenshot geometry and defer every image below the first preview."""
    loading = 'fetchpriority="high" loading="eager"' if eager else 'loading="lazy"'
    return f'<picture><source data-dark srcset="{BASE}assets/screenshots/{scene}-dark.png" media="(prefers-color-scheme: dark)"><img src="{BASE}assets/screenshots/{scene}-light.png" alt="{escape(alt)}" width="2400" height="1800" {loading} decoding="async"></picture>'


def render(locale, copy, release, template):
    """Compose localized semantic markup and metadata without client-side content rendering."""
    e = escape
    url = SITE + locale_path(locale)
    def download(compact=False):
        if release:
            return f'<a class="button {"compact" if compact else ""}" href="{release[2]}" data-download><span>{e(copy["nav"][2] if compact else copy["download"])}</span><span aria-hidden="true">↓</span></a>'
        if compact:
            return f'<a class="header-download" href="#download">{e(copy["soon"])} <span aria-hidden="true">↗</span></a>'
        return f'<button class="button unavailable" type="button" disabled><span>{e(copy["soon"])}</span><span aria-hidden="true">↓</span></button>'
    languages = ''.join(f'<a href="{BASE}{locale_path(key)}" lang="{key}" hreflang="{key}" {"aria-current=page" if key == locale else ""}>{e(name)}</a>' for key, name in LOCALES.items())
    theme_options = ''.join(f'<option value="{key}">{e(label)}</option>' for key, label in zip(['system', 'light', 'dark'], copy['themes']))
    hreflang = ''.join(f'<link rel="alternate" hreflang="{key}" href="{SITE}{locale_path(key)}">' for key in LOCALES)
    schema = {'@context': 'https://schema.org', '@type': 'SoftwareApplication', 'name': 'SpaceNeeded', 'applicationCategory': 'UtilitiesApplication', 'operatingSystem': 'macOS 27+', 'description': copy['description'], 'url': url, 'image': SITE + 'assets/brand/social.png', 'inLanguage': list(LOCALES)}
    if release:
        schema.update(softwareVersion=release[1], downloadUrl=release[2])
    sections = []
    # DerivedData anchors the hero; the other three scenes continue the story below.
    for index in [0, 2, 3]:
        title, detail, alt = copy['shots'][index]
        scene = SCENES[index]
        sections.append(f'''<article class="showcase reveal" aria-labelledby="shot-{scene}"><div class="showcase-copy"><p class="eyebrow">{['SETUP', 'XCODE', 'DOCKER', 'REVIEW'][index] if locale == 'en' else e([copy['nav'][0], 'Xcode', 'Docker', copy['safetyTitle']][index])}</p><h3 id="shot-{scene}">{e(title)}</h3><p>{e(detail)}</p></div><figure class="screen">{picture(scene, alt)}<figcaption class="sr-only">{e(alt)}</figcaption></figure></article>''')
    groups = []
    for group, (start, end) in enumerate(GROUPS):
        items = ''.join(f'<li data-source="{SOURCE_IDS[index]}">{e(copy["sources"][index])}</li>' for index in range(start, end))
        groups.append(f'<article class="source-group"><span class="source-mark" aria-hidden="true">{["⌘", "{ }", "[ ]", "◇", ">_", "⊞"][group]}</span><h3>{e(copy["groups"][group])}</h3><ul>{items}</ul><p class="source-note">{e(copy["sourceNotes"][group])}</p></article>')
    availability = e(copy['unavailable']) if not release else f'{e(copy["version"])} {release[1]}'
    values = {key: e(value) for key, value in copy.items() if isinstance(value, str)}
    values.update(locale=locale, base=BASE, canonical=url, hreflang=hreflang, schema=json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c'), icon=icon(34), heroIcon=icon(104), closeIcon=icon(64), headlineFirst=e(copy['headline'][0]), headlineSecond=e(copy['headline'][1]), navApp=e(copy['nav'][0]), navSources=e(copy['nav'][1]), navDownload=e(copy['nav'][2]), themeOptions=theme_options, languages=languages, currentLanguage=e(LOCALES[locale]), headerDownload=download(True), downloadButton=download(), availability=availability, heroPicture=picture('derived-data', copy['shots'][1][2], True), heroCaption=e(copy['shots'][1][0]), heroDetail=e(copy['shots'][1][1]), showcases=''.join(sections), sourceGroups=''.join(groups), closingHeadline='<br>'.join(e(copy['closingTitle']).split('\n')), ogLocale=OG_LOCALES[locale])
    return string.Template(template).substitute(values)


def build(output, appcast):
    """Render all pages before writing only the explicit managed outputs."""
    content = json.loads((ROOT / 'src/content.json').read_text())
    validate_content(content)
    release = release_info(appcast)
    template = (ROOT / 'src/page.html').read_text()
    pages = {locale_path(locale) + 'index.html': render(locale, copy, release, template) for locale, copy in content.items()}
    pages['sitemap.xml'] = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{SITE}{locale_path(locale)}</loc></url>' for locale in LOCALES) + '</urlset>\n'
    pages['404.html'] = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SpaceNeeded — Page not found</title><main><h1>Page not found</h1><p><a href="' + BASE + '">SpaceNeeded</a></p></main></html>\n'
    if set(pages) != set(GENERATED):
        raise ValueError('Unexpected output paths')
    output = output.resolve()
    for name in pages:
        target = output / name
        if target.is_symlink() or (target.parent != output and target.parent.is_symlink()):
            raise ValueError('Refusing redirected output')
    for name, html in pages.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html)
    print(f'Rendered {len(LOCALES)} languages; download: {release[1] if release else "coming soon"}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--appcast', type=Path, default=ROOT / 'appcast.xml')
    parser.add_argument('--output', type=Path, default=ROOT)
    parser.add_argument('--list-outputs', action='store_true')
    args = parser.parse_args()
    if args.list_outputs:
        print(json.dumps(GENERATED))
    else:
        build(args.output, args.appcast)
