import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const lang = z.enum(['en', 'da']);
const optionalText = z
  .string()
  .optional()
  .nullable()
  .transform((v) => (v ? v : undefined));

const posts = defineCollection({
  loader: glob({ pattern: '*.mdoc', base: './src/content/posts' }),
  schema: z.object({
    title: z.string(),
    lang,
    date: z.coerce.date(),
    kind: z.enum(['note', 'essay']).default('note'),
    summary: optionalText,
    translationKey: optionalText,
    draft: z.boolean().default(false),
  }),
});

const projects = defineCollection({
  loader: glob({ pattern: '*.mdoc', base: './src/content/projects' }),
  schema: z.object({
    title: z.string(),
    lang,
    year: z.number().int(),
    summary: optionalText,
    link: optionalText,
    featured: z.boolean().default(false),
    translationKey: optionalText,
  }),
});

const photos = defineCollection({
  loader: glob({ pattern: '*.yaml', base: './src/content/photos' }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      image: image(),
      date: z.coerce.date(),
      place: optionalText,
      captionEn: optionalText,
      captionDa: optionalText,
    }),
});

const books = defineCollection({
  loader: glob({ pattern: '*.yaml', base: './src/content/books' }),
  schema: z.object({
    title: z.string(),
    creator: optionalText,
    type: z.enum(['book', 'album', 'film', 'series']).default('book'),
    status: z.enum(['current', 'finished', 'next']).default('current'),
    date: z.coerce.date().optional().nullable(),
    noteEn: optionalText,
    noteDa: optionalText,
  }),
});

const pages = defineCollection({
  loader: glob({ pattern: '*.mdoc', base: './src/content/pages' }),
  schema: z.object({
    title: z.string(),
    updated: z.coerce.date().optional().nullable(),
  }),
});

const settings = defineCollection({
  loader: glob({ pattern: '*.yaml', base: './src/content/settings' }),
  schema: z.object({
    email: optionalText,
    buttondownUsername: optionalText,
    links: z.array(z.object({ label: z.string(), url: z.string() })).default([]),
  }),
});

export const collections = { posts, projects, photos, books, pages, settings };
