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
- **Weeks**: a week log, one sentence a week about what I'm doing (replaced the Now page, which only repeated other pages). Links to elsewhere live in the footer

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

**Visual decisions (from three rounds of type/colour review):**
- **Colour:** Pine. Light: paper `#EEF0EB`, ink `#121614`, accent `#1F6B47`, muted `#66706B`. Dark: paper `#101411`, ink `#E5EAE6`, accent `#62C795`, muted `#8E9893`
- **Text:** IBM Plex Sans for body copy, IBM Plex Mono for dates, navigation and labels
- **Headline:** **Schibsted Grotesk** (bold weights) for the name, headlines and section titles, with letter spacing `+0.05rem`

**Tension to keep in balance:** the calm editorial layout and the characterful display face pull in different directions. Use the display face loudly in a few places (name, section titles) and keep everything else quiet.

## Layout (after the "less AI" pass)

- **Weekly notebook:** every page has a left margin column for context (week numbers, dates, section names, the reading line) and a ~42rem reading column. Left aligned; the right side of wide screens stays open
- **Hero:** the latest week-log sentence as the big headline. The margin says "Week 46, 2026": the ISO week of that entry, since Danes date things by week number
- **Weeks grid (flair):** the year as 52 small squares under the hero label (and on the Writing page). Weeks with a post or photo are pine and link to it; this week breathes; a nod to *Four Thousand Weeks*
- **Print texture (flair):** a fine fixed paper grain over the page, and every pine mark printed twice, the second pass a pixel off, like a risograph
- **Pine** only on underlines, rules and the reading line. **Plex Mono** only for numbers in the margin
- **Avoided on purpose:** all-caps labels, an accent-coloured word in headlines, `→` on links, dot-joined meta strings, rounded cards

## Signature moments (launch)

1. **Underline → heading**: when a post link is clicked, its pine underline lifts off and stretches into the rule under the post title. Going back reverses it. Built with the View Transitions API (Astro `<ClientRouter />`), with a plain page load as fallback
2. **Reading line**: on essays and long notes, a thin pine line with a dot at its tip draws down the margin as you read

Both respect `prefers-reduced-motion` (no animation; the end state is shown). Considered and dropped: name settling in, living pine dot, bookshelf spines.

## Type hierarchy

| Level | Role | Style |
|---|---|---|
| 1 | One per page: homepage sentence, page title, post title | Schibsted Grotesk 800, large |
| 2 | List items: post, project and book titles; prose subheads | Schibsted Grotesk 600, 1.375rem |
| 3 | Reading text | IBM Plex Sans 400, 17px |
| Margin | Context only: section names, week labels, dates | IBM Plex Sans 500, 15px; numbers in Plex Mono |

The wordmark stays Schibsted 800 (it's the logo). Book titles in running text are italic. Pull quotes are italic with a pine rule, never larger than a subhead.

## Ideas for later

- **Handwritten margins:** margin notes, photo captions and week labels in Magnus's own handwriting (scanned and turned into a font), like annotations in a notebook. Fits the margin column and the "honest" value

## Technical direction

| | Recommendation |
|---|---|
| **Domain** | **magnushkaspersen.com** (primary). **magnus.hk** as a short alias that redirects to it, if the renewal at Alibaba goes through |
| **Framework** | Astro: static, fast, has built-in i18n routing and content collections |
| **Editing** | A simple CMS. Recommended: **Keystatic** or **Decap CMS**. Both are git-based, give a web UI for writing, and need no database |
| **Hosting** | **Cloudflare** Pages/Workers |
| **Contact form** | Cloudflare Worker / Pages Function, sent to email, with Turnstile for spam |
| **Newsletter** | An external service (e.g. Buttondown), plus RSS feeds from Astro |
| **i18n** | `/en/` and `/da/` routes. A post can exist in one language or both. Show a note when a translation is missing |
| **Photos** | Astro image optimisation; photos stored in the repo or in Cloudflare R2 if the library grows |

## Build status

The site skeleton is built: all sections in EN and DA, Keystatic editing, RSS, sitemap, the contact endpoint and both signature moments. See `README.md` for running, editing and deploying. All content is still sample copy.

## Open questions (for later)

- Newsletter provider and whether it sends automatically from new posts
- Write the real About text (EN + DA)
- Set up Cloudflare deploy, Keystatic GitHub App, Resend and Turnstile secrets
