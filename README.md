# SpaceNeeded

Make room for your next build. SpaceNeeded is a native Mac app to inspect developer caches, build artifacts and other cleanup candidates, choose what goes, and review every cleanup.

Requires **macOS 27 or later** and **Apple Silicon**. [Download the latest release](https://github.com/legranddamien/space-needed/releases/latest/download/SpaceNeeded.dmg).

[Visit the website](https://legranddamien.github.io/space-needed/).

## Website development

This repository contains the public website, Sparkle feed and release assets. It does not contain the macOS application source. GitHub Pages serves `main` at the root, including the `/space-needed/` URL prefix.

Build all nine localized pages with Python 3.11 or later, with no third-party dependencies:

```sh
python3 scripts/build.py
python3 scripts/check.py
python3 scripts/serve.py
```

Open `http://localhost:8000/space-needed/`. `src/content.json` owns translated copy; `src/page.html` owns shared markup. CSS and JavaScript live under `assets/`. Generated locale HTML and `sitemap.xml` are committed alongside their sources. Never hand-edit generated pages.

The build accepts `--appcast PATH` and `--output DIRECTORY` for preflight checks. `--list-outputs` returns its managed page paths as JSON. The app repository's release publisher validates a temporary build before publication, then regenerates these pages from the verified release feed. An empty feed renders “Coming soon”; no download is advertised until a release is present. Preserve the homepage's single `download:start` / `download:end` marker pair.

The website supports English, French, German, Spanish, Italian, Japanese, Korean, Brazilian Portuguese and Simplified Chinese. Language links keep separate crawlable URLs. Theme defaults to the system and can be overridden locally. English screenshots have localized descriptions and switch with the theme. The app repository owns their capture/export workflow; retain the eight managed PNG names and manifest under `assets/screenshots/`.

The site uses no analytics, cookies or remote fonts. Theme and animation preferences are stored locally when browser storage is available. Motion respects reduced-motion settings. The sitemap lives at `/space-needed/sitemap.xml`; robots directives would need to be served from the domain root and are therefore not placed in this project directory.

Before publication, run the checks and inspect all languages on desktop and mobile in both themes. Translation copy has not received independent native-speaker review. Use the app at your own risk: review every selection and keep backups; some cleanup actions permanently delete data.

Optional browser QA uses Node.js, Chrome, Playwright and axe. Run `npm ci`, start the preview server, then run `npm run test:browser`. It checks all locales at 320, 390, 768 and 1440px in both themes, audits accessibility with reduced motion enabled, verifies theme/system behavior and saves local reports under ignored `.qa/`. `SITE_URL` can override the preview URL. The static build itself does not need Node.js.
