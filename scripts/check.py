#!/usr/bin/env python3
"""Validate generated content, localization and release states without network access."""
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import tempfile
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location('site_build', Path(__file__).with_name('build.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class Document(HTMLParser):
    """Collect semantic and resource references from rendered pages."""
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def rejects(action):
    """Require invalid inputs to fail before any output is advertised."""
    try:
        action()
    except (ValueError, ET.ParseError):
        return
    raise AssertionError('Expected rejection')


content = json.loads((b.ROOT / 'src/content.json').read_text())
b.validate_content(content)
assert len(set(b.SOURCE_IDS)) == 18
broken = json.loads(json.dumps(content))
broken['ja'].pop('risk')
rejects(lambda: b.validate_content(broken))
with tempfile.TemporaryDirectory(prefix='spaceneeded-site-check-') as temporary:
    root = Path(temporary)
    feed = root / 'appcast.xml'
    feed.write_text('<rss><channel/></rss>')
    b.build(root / 'empty', feed)
    for locale in b.LOCALES:
        path = b.locale_path(locale) + 'index.html'
        text = (root / 'empty' / path).read_text()
        doc = Document(text)
        assert text.count('<!-- download:start -->') == text.count('<!-- download:end -->') == 1
        assert 'data-download' not in text
        assert [attrs['lang'] for tag, attrs in doc.tags if tag == 'html'] == [locale]
        assert sum(tag == 'h1' for tag, _ in doc.tags) == 1
        alternates = [a for t, a in doc.tags if t == 'link' and a.get('rel') == 'alternate']
        assert {a['hreflang'] for a in alternates} == set(b.LOCALES) | {'x-default'}
        assert all(a['href'].startswith(b.SITE) for a in alternates)
        assert [a['href'] for t, a in doc.tags if t == 'link' and a.get('rel') == 'canonical'] == [b.SITE + b.locale_path(locale)]
        assert {a['data-source'] for _, a in doc.tags if 'data-source' in a} == set(b.SOURCE_IDS)
        ids = [a['id'] for _, a in doc.tags if 'id' in a]
        assert len(ids) == len(set(ids))
        for tag, attrs in doc.tags:
            for key in ['src', 'srcset', 'href']:
                value = attrs.get(key, '')
                if value.startswith('#'):
                    assert value[1:] in ids, (locale, value)
                if value.startswith(b.BASE + 'assets/'):
                    assert (b.ROOT / value[len(b.BASE):]).is_file(), value
            if tag == 'img':
                assert all(key in attrs for key in ['alt', 'width', 'height'])
        assert content[locale]['risk'] in text
    feed.write_text('<rss xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle"><channel><item><sparkle:version>42</sparkle:version><sparkle:shortVersionString>1.2.3</sparkle:shortVersionString><enclosure url="https://github.com/legranddamien/space-needed/releases/download/v1.2.3/SpaceNeeded.dmg"/></item></channel></rss>')
    b.build(root / 'released', feed)
    for locale in b.LOCALES:
        text = (root / 'released' / b.locale_path(locale) / 'index.html').read_text()
        assert text.count('data-download') == 3
        downloads = [attrs['href'] for tag, attrs in Document(text).tags if tag == 'a' and 'data-download' in attrs]
        assert downloads == ['https://github.com/legranddamien/space-needed/releases/latest/download/SpaceNeeded.dmg'] * 3
        assert '"downloadUrl": "https://github.com/legranddamien/space-needed/releases/latest/download/SpaceNeeded.dmg"' in text
        assert '"softwareVersion": "1.2.3"' in text
        assert 'disabled' not in text
    feed.write_text(feed.read_text().replace('https://github.com/legranddamien/', 'https://example.com/'))
    rejects(lambda: b.build(root / 'invalid', feed))
    assert not (root / 'invalid').exists()
    feed.write_text('<rss>')
    rejects(lambda: b.release_info(feed))
    # Confirm committed generated pages match their source content and current feed.
    b.build(root / 'current', b.ROOT / 'appcast.xml')
    for name in b.GENERATED:
        assert (root / 'current' / name).read_bytes() == (b.ROOT / name).read_bytes(), f'Stale generated page: {name}'
print('Passed: 9 locales, 18 source IDs, links/assets, SEO, empty/released feeds, invalid feeds and deterministic generated output.')
