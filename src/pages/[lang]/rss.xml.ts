import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { langPaths, t, url, type Lang } from '~/i18n';
import { getPosts } from '~/lib/content';

export const getStaticPaths = langPaths;

export async function GET(context: APIContext) {
  const lang = context.params.lang as Lang;
  const posts = await getPosts(lang);
  return rss({
    title: 'Magnus H. Kaspersen',
    description: t(lang, 'site.description'),
    site: context.site!,
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.date,
      description: post.data.summary,
      link: url(lang, 'writing', post.id),
    })),
    customData: `<language>${lang === 'da' ? 'da-dk' : 'en-gb'}</language>`,
  });
}
