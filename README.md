# magnushkaspersen.com

A bilingual (English / Danish) digital home. The brief and every design decision are in [`PROFILE.md`](PROFILE.md).

- **Astro 7**, static by default, deployed to **Cloudflare Workers**
- **Keystatic** for editing content in a web UI (no database: content lives as files in this repo)
- Pine palette, **Schibsted Grotesk** headlines, **IBM Plex Sans/Mono** text, all fonts self-hosted
- Two signature moments: the **underline → heading** page transition and the **reading line** on essays

> All content in `src/content/` is sample copy, and the photos are generated placeholders. Replace them before launch.

## Run it locally

```sh
npm install
npm run dev          # http://localhost:4321  (Keystatic at /keystatic)
```

`npm run dev` runs on Node so that Keystatic can write straight to the files on disk. To try the real Cloudflare runtime locally, run `npm run build && npm run preview`.

## Writing and editing

Open **/keystatic**. In local dev it edits the files in `src/content/`. In production it commits to GitHub, which triggers a deploy.

| In Keystatic | Lives in | Notes |
|---|---|---|
| Writing | `src/content/posts/*.mdoc` | Choose **Essay** to get the reading line. Give the English and Danish versions the same *translation key* to link them |
| Projects | `src/content/projects/*.mdoc` | Tick *Show on the homepage* to feature a project |
| Photos | `src/content/photos/*.yaml` + `src/assets/photos/` | Optimised to WebP at build time |
| Bookshelf & media | `src/content/books/*.yaml` | Status: currently / up next / finished |
| Weeks | `src/content/weeks/*.yaml` | One sentence a week (EN + DA). The newest is the homepage headline; all of them make up the Weeks page |
| About (EN + DA) | `src/content/pages/*.mdoc` | |
| Site settings | `src/content/settings/site.yaml` | Email, links, Buttondown username for the newsletter |

A post can exist in one language only. The page then says so, and the language switch goes to the other language's homepage section.

## Deploying to Cloudflare

1. In Cloudflare: **Workers & Pages → Create → Import a repository**, pick this repo. Build command `npm run build`, deploy command `npx wrangler deploy`.
2. Under the worker's **Domains & Routes**, add `magnushkaspersen.com` and `www.magnushkaspersen.com`. If you renew `magnus.hk`, add a redirect rule that sends it to `https://magnushkaspersen.com`.
3. Add the secrets below under **Settings → Variables and secrets**.

### Keystatic in production (GitHub mode)

1. Run `npm run dev`, open `/keystatic`, and switch `storage` to GitHub mode temporarily (or follow Keystatic's prompt). It walks you through creating a GitHub App and writes the four `KEYSTATIC_*` values to `.env`.
2. Copy those values into Cloudflare as secrets: `KEYSTATIC_GITHUB_CLIENT_ID`, `KEYSTATIC_GITHUB_CLIENT_SECRET`, `KEYSTATIC_SECRET`, and `PUBLIC_KEYSTATIC_GITHUB_APP_SLUG` (a build-time variable).
3. In the GitHub App settings, set the callback URL to `https://magnushkaspersen.com/api/keystatic/github/oauth/callback`.

If the repository is renamed, update `repo` in `keystatic.config.ts`.

### Contact form

The form posts to `/api/contact`. That endpoint checks Cloudflare Turnstile, if configured, and sends email through [Resend](https://resend.com). Set these secrets:

- `TURNSTILE_SITE_KEY` (public) and `TURNSTILE_SECRET_KEY`
- `RESEND_API_KEY`, `CONTACT_TO_EMAIL`, `CONTACT_FROM_EMAIL` (a sender on a domain verified in Resend)

Without them, the form politely asks people to email you directly.

### Newsletter

Add your Buttondown username in **Site settings** and the signup form appears in the footer. Readers are tagged `en` or `da`. RSS feeds are at `/en/rss.xml` and `/da/rss.xml`.

## Project map

```
src/
  i18n.ts                 UI strings (EN/DA), URL and date helpers
  content.config.ts       Content schemas (mirrors keystatic.config.ts)
  styles/global.css       Design tokens, type, prose, view-transition timing
  layouts/Base.astro      <head>, header, footer, ClientRouter
  components/
    EntryList.astro       Dated link lists; underlines carry the transition name
    Article.astro         Post/project layout with the matching heading rule
    ReadingLine.astro     The reading line
  pages/
    index.astro           Root: sends visitors to /da/ or /en/
    [lang]/...            All pages, generated for en and da
    api/contact.ts        Contact form endpoint (runs on demand)
```
