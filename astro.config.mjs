// @ts-check
import { defineConfig, envField } from 'astro/config';
import cloudflare from '@astrojs/cloudflare';
import react from '@astrojs/react';
import markdoc from '@astrojs/markdoc';
import sitemap from '@astrojs/sitemap';
import keystatic from '@keystatic/astro';

// `astro dev` runs on Node so Keystatic can edit files on disk (its local
// mode needs Node). Builds and `wrangler dev` use the Cloudflare adapter.
const isDev = process.argv.includes('dev');

export default defineConfig({
  site: 'https://magnushkaspersen.com',
  trailingSlash: 'ignore',

  // Pages are prerendered by default. Only the contact endpoint and the
  // Keystatic admin (/keystatic) run on demand on Cloudflare.
  output: 'static',
  adapter: isDev
    ? undefined
    : cloudflare({
        // Optimise images at build time; no Cloudflare Images binding needed.
        imageService: 'compile',
      }),
  // No logins or carts on this site, so no session storage (and no KV binding).
  session: false,

  integrations: [react(), markdoc(), keystatic(), sitemap({
    i18n: { defaultLocale: 'en', locales: { en: 'en', da: 'da' } },
    filter: (page) => !page.includes('/keystatic') && !page.includes('/api/'),
  })],

  i18n: {
    locales: ['en', 'da'],
    defaultLocale: 'en',
    routing: { prefixDefaultLocale: true, redirectToDefaultLocale: false },
  },

  env: {
    schema: {
      TURNSTILE_SITE_KEY: envField.string({ context: 'client', access: 'public', optional: true }),
      TURNSTILE_SECRET_KEY: envField.string({ context: 'server', access: 'secret', optional: true }),
      RESEND_API_KEY: envField.string({ context: 'server', access: 'secret', optional: true }),
      CONTACT_TO_EMAIL: envField.string({ context: 'server', access: 'secret', optional: true }),
      CONTACT_FROM_EMAIL: envField.string({ context: 'server', access: 'secret', optional: true }),
    },
  },

  prefetch: { prefetchAll: true },

  vite: {
    // Keystatic ships some CommonJS. Pre-bundle it so the admin (/keystatic)
    // also runs inside Cloudflare's workerd runtime.
    optimizeDeps: {
      include: ['@keystatic/core', '@keystatic/core/ui', '@keystatic/core/api/generic', '@keystatic/astro/ui', '@keystatic/astro/api'],
    },
  },
});
