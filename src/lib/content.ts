import { getCollection, getEntry, type CollectionEntry } from 'astro:content';
import { isoWeek, type Lang } from '~/i18n';

export const getPosts = async (lang: Lang) =>
  (await getCollection('posts', ({ data }) => data.lang === lang && (import.meta.env.DEV || !data.draft))).sort(
    (a, b) => b.data.date.valueOf() - a.data.date.valueOf(),
  );

export const getProjects = async (lang: Lang) =>
  (await getCollection('projects', ({ data }) => data.lang === lang)).sort((a, b) => b.data.year - a.data.year);

export const getPhotos = async () =>
  (await getCollection('photos')).sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());

export const getBooks = async () =>
  (await getCollection('books')).sort((a, b) => (b.data.date?.valueOf() ?? 0) - (a.data.date?.valueOf() ?? 0));

export const getPage = (name: 'about', lang: Lang) => getEntry('pages', `${name}-${lang}`);

/** Week log entries, newest first. Danish falls back to English if not translated. */
export const getWeeks = async () =>
  (await getCollection('weeks')).sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());

export const weekText = (entry: CollectionEntry<'weeks'>, lang: Lang) =>
  (lang === 'da' ? entry.data.textDa : undefined) ?? entry.data.textEn;

/** Anchor id for a week on the Weeks page, e.g. w2026-46. */
export const weekAnchor = (date: Date) => {
  const { week, year } = isoWeek(date);
  return `w${year}-${week}`;
};

export const getSettings = async () => {
  const entry = await getEntry('settings', 'site');
  return entry?.data ?? { email: undefined, buttondownUsername: undefined, links: [] };
};

/** The same piece in the other language, if one has the same translation key. */
export async function getTranslation<C extends 'posts' | 'projects'>(
  collection: C,
  entry: CollectionEntry<C>,
): Promise<CollectionEntry<C> | undefined> {
  const key = entry.data.translationKey;
  if (!key) return undefined;
  const all = (await getCollection(collection)) as CollectionEntry<C>[];
  return all.find((e) => e.data.translationKey === key && e.data.lang !== entry.data.lang);
}

/** Stable view-transition name shared by a list link's underline and the post's heading rule. */
export const ruleName = (collection: string, id: string) => `rule-${collection}-${id}`;

export const readingMinutes = (body = '') => Math.max(1, Math.round(body.split(/\s+/).filter(Boolean).length / 220));
