import { config, collection, singleton, fields } from '@keystatic/core';

const lang = fields.select({
  label: 'Language',
  options: [
    { label: 'English', value: 'en' },
    { label: 'Dansk', value: 'da' },
  ],
  defaultValue: 'en',
});

const translationKey = fields.text({
  label: 'Translation key',
  description:
    'Give the English and Danish versions of the same piece the same key (e.g. "first-month"). Leave empty if it only exists in one language.',
});

const pageSingleton = (label: string, path: string) =>
  singleton({
    label,
    path,
    format: { contentField: 'content' },
    schema: {
      title: fields.text({ label: 'Title' }),
      updated: fields.date({ label: 'Last updated', defaultValue: { kind: 'today' } }),
      content: fields.markdoc({ label: 'Content' }),
    },
  });

export default config({
  // Locally, Keystatic edits the files on disk. In production it commits to
  // GitHub, so publishing from /keystatic triggers a Cloudflare deploy.
  storage: import.meta.env.PROD
    ? { kind: 'github', repo: 'magniswerfer/my-new-website-again' }
    : { kind: 'local' },

  ui: {
    brand: { name: 'magnushkaspersen.com' },
    navigation: {
      Write: ['weeks', 'posts', 'projects'],
      Collect: ['photos', 'books'],
      Pages: ['aboutEn', 'aboutDa', 'settings'],
    },
  },

  collections: {
    weeks: collection({
      label: 'Weeks',
      slugField: 'name',
      path: 'src/content/weeks/*',
      format: 'yaml',
      columns: ['name', 'date'],
      schema: {
        name: fields.slug({
          name: { label: 'Name', description: 'Just for you, e.g. "2026 week 46".' },
        }),
        date: fields.date({
          label: 'Any day in the week',
          description: 'The site works out the week number from this.',
          defaultValue: { kind: 'today' },
          validation: { isRequired: true },
        }),
        textEn: fields.text({ label: 'This week (English)', multiline: true, validation: { length: { min: 1 } } }),
        textDa: fields.text({ label: 'Denne uge (Dansk)', multiline: true }),
      },
    }),

    posts: collection({
      label: 'Writing',
      slugField: 'title',
      path: 'src/content/posts/*',
      format: { contentField: 'content' },
      entryLayout: 'content',
      columns: ['title', 'date', 'lang'],
      schema: {
        title: fields.slug({ name: { label: 'Title' } }),
        lang,
        date: fields.date({ label: 'Date', defaultValue: { kind: 'today' }, validation: { isRequired: true } }),
        kind: fields.select({
          label: 'Kind',
          options: [
            { label: 'Note (short)', value: 'note' },
            { label: 'Essay (long, gets the reading line)', value: 'essay' },
          ],
          defaultValue: 'note',
        }),
        summary: fields.text({ label: 'Summary', multiline: true }),
        translationKey,
        draft: fields.checkbox({ label: 'Draft (hidden from the site)', defaultValue: false }),
        content: fields.markdoc({ label: 'Content' }),
      },
    }),

    projects: collection({
      label: 'Projects',
      slugField: 'title',
      path: 'src/content/projects/*',
      format: { contentField: 'content' },
      columns: ['title', 'year', 'lang'],
      schema: {
        title: fields.slug({ name: { label: 'Title' } }),
        lang,
        year: fields.integer({ label: 'Year', defaultValue: new Date().getFullYear() }),
        summary: fields.text({ label: 'One-line summary' }),
        link: fields.url({ label: 'External link (optional)' }),
        featured: fields.checkbox({ label: 'Show on the homepage', defaultValue: false }),
        translationKey,
        content: fields.markdoc({ label: 'Content' }),
      },
    }),

    photos: collection({
      label: 'Photos',
      slugField: 'title',
      path: 'src/content/photos/*',
      format: 'yaml',
      columns: ['title', 'date'],
      schema: {
        title: fields.slug({ name: { label: 'Title (for your reference)' } }),
        image: fields.image({
          label: 'Photo',
          directory: 'src/assets/photos',
          publicPath: '../../assets/photos/',
          validation: { isRequired: true },
        }),
        date: fields.date({ label: 'Date taken', defaultValue: { kind: 'today' }, validation: { isRequired: true } }),
        place: fields.text({ label: 'Place' }),
        captionEn: fields.text({ label: 'Caption (English)' }),
        captionDa: fields.text({ label: 'Caption (Dansk)' }),
      },
    }),

    books: collection({
      label: 'Bookshelf & media',
      slugField: 'title',
      path: 'src/content/books/*',
      format: 'yaml',
      columns: ['title', 'creator', 'status'],
      schema: {
        title: fields.slug({ name: { label: 'Title' } }),
        creator: fields.text({ label: 'Author / artist / director' }),
        type: fields.select({
          label: 'Type',
          options: [
            { label: 'Book', value: 'book' },
            { label: 'Album', value: 'album' },
            { label: 'Film', value: 'film' },
            { label: 'Series', value: 'series' },
          ],
          defaultValue: 'book',
        }),
        status: fields.select({
          label: 'Status',
          options: [
            { label: 'Currently', value: 'current' },
            { label: 'Finished', value: 'finished' },
            { label: 'Up next', value: 'next' },
          ],
          defaultValue: 'current',
        }),
        date: fields.date({ label: 'Started / finished', defaultValue: { kind: 'today' } }),
        noteEn: fields.text({ label: 'Note (English)', multiline: true }),
        noteDa: fields.text({ label: 'Note (Dansk)', multiline: true }),
      },
    }),
  },

  singletons: {
    aboutEn: pageSingleton('About (English)', 'src/content/pages/about-en'),
    aboutDa: pageSingleton('Om (Dansk)', 'src/content/pages/about-da'),
    settings: singleton({
      label: 'Site settings',
      path: 'src/content/settings/site',
      format: 'yaml',
      schema: {
        email: fields.text({ label: 'Public email address' }),
        buttondownUsername: fields.text({
          label: 'Buttondown username',
          description: 'For the newsletter form. Leave empty to hide the form.',
        }),
        links: fields.array(
          fields.object({
            label: fields.text({ label: 'Label' }),
            url: fields.url({ label: 'URL' }),
          }),
          { label: 'Elsewhere (links)', itemLabel: (props) => props.fields.label.value || 'Link' },
        ),
      },
    }),
  },
});
