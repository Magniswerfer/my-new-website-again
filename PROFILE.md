# Site profile

The brief for the new site, based on the interview of 11 Nov 2026. Use it to make design and build decisions.

## In one line

A calm, editorial, bilingual (EN/DA) digital home for a personal reinvention. It changes often, is personal but curated, and is written in a reflective voice.

## Purpose & audience

| | |
|---|---|
| **Job of the site** | A digital home: about, writing, projects and links in one place |
| **Why now** | Personal reinvention. The site shows who I am *now* |
| **For** | Peers in my field, friends & community, curious strangers |
| **Not primarily for** | Clients or employers. No sales funnel, no "hire me" pressure |
| **Languages** | English + Danish, with a visible language switch |

## Content

**Core sections**
- **About / story**: who I am now, and the shift that got me here
- **Writing / notes**: essays and shorter notes, the main thing that changes on the site
- **Projects / things I make**: work, side projects, experiments
- **Now + links**: what I'm up to this month, plus where to find me

**Extras**
- **Photos / visual diary**: a photo stream
- **Bookshelf / media log**: books, music and films, with short notes
- **Newsletter + RSS**: ways to follow along
- **Contact form**: in addition to an email link

**Cadence:** weekly or more often. Adding things has to be fast and easy, or it won't happen.

**Openness:** personal but curated. Warm and human, with clear boundaries.

## Voice

- **Reflective**: quiet, essay-like, written in the first person
- Visitors should come away thinking it feels **thoughtful, curious, honest, crafted**
- Honest means I can say "I'm figuring this out"; crafted means the details are still deliberate

## Aesthetics

| | Direction | What it means in practice |
|---|---|---|
| **Mood** | Calm & editorial | Generous whitespace, a strong reading column, magazine-like rhythm |
| **Colour** | Off-white + ink | Warm paper background, near-black text, **one** accent colour used sparingly. Dark mode is the same idea inverted (ink background, paper text) |
| **Type** | Characterful display | One distinctive headline face that *is* the identity, paired with a quiet, very readable text face |
| **Motion** | A few signature moments | Mostly still. One or two memorable interactions (e.g. the homepage name/intro, the language switch, or page transitions). Everything else stays calm |

**Tension to keep in balance:** the calm editorial layout and the characterful display face pull in different directions. Use the display face loudly in a few places (name, section titles) and keep everything else quiet.

## Technical direction

| | Recommendation |
|---|---|
| **Framework** | Astro: static, fast, has built-in i18n routing and content collections |
| **Editing** | A simple CMS. Recommended: **Keystatic** or **Decap CMS**. Both are git-based, give a web UI for writing, and need no database |
| **Hosting** | **Cloudflare** Pages/Workers |
| **Contact form** | Cloudflare Worker / Pages Function, sent to email, with Turnstile for spam |
| **Newsletter** | An external service (e.g. Buttondown), plus RSS feeds from Astro |
| **i18n** | `/en/` and `/da/` routes. A post can exist in one language or both. Show a note when a translation is missing |
| **Photos** | Astro image optimisation; photos stored in the repo or in Cloudflare R2 if the library grows |

## Open questions (for later)

- Name / domain for the site
- Which accent colour and which display typeface. Next step: a few type + colour pairings to choose between
- Should the existing personal design system be reused, or should the "new me" get a fresh visual identity?
- Which signature moment(s) to build first
- Newsletter provider and whether it sends automatically from new posts
