export const langs = ['en', 'da'] as const;
export type Lang = (typeof langs)[number];

export const langPaths = () => langs.map((lang) => ({ params: { lang } }));
export const other = (lang: Lang): Lang => (lang === 'en' ? 'da' : 'en');

const ui = {
  en: {
    'site.description': 'Magnus H. Kaspersen writes, makes things and keeps notes on what changes.',
    'nav.about': 'About',
    'nav.writing': 'Writing',
    'nav.projects': 'Projects',
    'nav.photos': 'Photos',
    'nav.bookshelf': 'Bookshelf',
    'nav.weeks': 'Weeks',
    'nav.contact': 'Contact',
    'nav.skip': 'Skip to content',
    'lang.switch': 'Dansk',
    'lang.switchLabel': 'Læs på dansk',
    'home.week': 'Week',
    'home.intro': "I'm Magnus. I'm starting over, and I write here most weeks about that, and about what I make and read along the way.",
    'home.latest': 'Writing',
    'home.allWriting': 'All writing',
    'home.projects': 'Projects',
    'home.allProjects': 'All projects',
    'home.earlier': 'Earlier weeks',
    'home.photos': 'Photos',
    'home.allPhotos': 'All photos',
    'home.reading': 'Reading',
    'post.back': 'Writing',
    'post.essay': 'Essay',
    'post.note': 'Note',
    'post.min': 'min read',
    'post.alsoIn': 'Read this in Danish',
    'post.onlyIn': 'This piece is only in English.',
    'project.back': 'Projects',
    'project.visit': 'Visit project',
    'writing.title': 'Writing',
    'writing.intro': 'Essays and shorter notes, newest first.',
    'projects.title': 'Projects',
    'projects.intro': 'Things I make: work, side projects and experiments.',
    'photos.title': 'Photos',
    'photos.intro': 'A visual diary.',
    'books.title': 'Bookshelf',
    'books.intro': "Books, music and films I'm spending time with.",
    'books.current': 'Reading now',
    'books.finished': 'Finished',
    'books.next': 'Up next',
    'weeks.title': 'Weeks',
    'weeks.intro': 'One sentence a week about what I’m doing, newest first.',
    'now.elsewhere': 'Elsewhere',
    'contact.title': 'Contact',
    'contact.intro': 'Write to me. I read everything, and reply to most.',
    'contact.name': 'Name',
    'contact.email': 'Your email',
    'contact.message': 'Message',
    'contact.send': 'Send message',
    'contact.or': 'Or email me directly at',
    'contact.error': "Your message couldn't be sent. Please try again, or email me directly.",
    'contact.sentTitle': 'Thanks, your message is on its way',
    'contact.sentBody': "I'll get back to you as soon as I can.",
    'contact.back': 'Back to the homepage',
    'footer.follow': 'Follow along',
    'footer.newsletter': 'Get new writing by email, about once a month.',
    'footer.emailLabel': 'Email address',
    'footer.subscribe': 'Subscribe',
    'footer.rss': 'RSS feed',
    'footer.write': 'Write to me at',
    'footer.orForm': 'or use the',
    'footer.form': 'contact form',
    'footer.follow2': 'Follow new writing by',
    'notfound.title': 'This page has moved on',
    'notfound.body': "There's nothing at this address. Try the homepage or the writing archive.",
  },
  da: {
    'site.description': 'Magnus H. Kaspersen skriver, laver ting og holder styr på, hvad der ændrer sig.',
    'nav.about': 'Om',
    'nav.writing': 'Skrivning',
    'nav.projects': 'Projekter',
    'nav.photos': 'Fotos',
    'nav.bookshelf': 'Bogreol',
    'nav.weeks': 'Uger',
    'nav.contact': 'Kontakt',
    'nav.skip': 'Gå til indhold',
    'lang.switch': 'English',
    'lang.switchLabel': 'Read in English',
    'home.week': 'Uge',
    'home.intro': 'Jeg er Magnus. Jeg er ved at starte forfra, og jeg skriver her de fleste uger om det, og om det jeg laver og læser undervejs.',
    'home.latest': 'Skrivning',
    'home.allWriting': 'Alt skrevet',
    'home.projects': 'Projekter',
    'home.allProjects': 'Alle projekter',
    'home.earlier': 'Tidligere uger',
    'home.photos': 'Fotos',
    'home.allPhotos': 'Alle fotos',
    'home.reading': 'Læser',
    'post.back': 'Skrivning',
    'post.essay': 'Essay',
    'post.note': 'Note',
    'post.min': 'min læsning',
    'post.alsoIn': 'Læs den på engelsk',
    'post.onlyIn': 'Denne tekst findes kun på dansk.',
    'project.back': 'Projekter',
    'project.visit': 'Besøg projektet',
    'writing.title': 'Skrivning',
    'writing.intro': 'Essays og kortere noter, nyeste først.',
    'projects.title': 'Projekter',
    'projects.intro': 'Ting jeg laver: arbejde, sideprojekter og eksperimenter.',
    'photos.title': 'Fotos',
    'photos.intro': 'En visuel dagbog.',
    'books.title': 'Bogreol',
    'books.intro': 'Bøger, musik og film, jeg bruger tid på.',
    'books.current': 'Læser nu',
    'books.finished': 'Færdig',
    'books.next': 'Næste',
    'weeks.title': 'Uger',
    'weeks.intro': 'Én sætning om ugen om, hvad jeg laver. Nyeste først.',
    'now.elsewhere': 'Andre steder',
    'contact.title': 'Kontakt',
    'contact.intro': 'Skriv til mig. Jeg læser alt og svarer på det meste.',
    'contact.name': 'Navn',
    'contact.email': 'Din e-mail',
    'contact.message': 'Besked',
    'contact.send': 'Send besked',
    'contact.or': 'Eller skriv direkte til',
    'contact.error': 'Din besked kunne ikke sendes. Prøv igen, eller skriv direkte til mig.',
    'contact.sentTitle': 'Tak, din besked er sendt',
    'contact.sentBody': 'Jeg vender tilbage, så snart jeg kan.',
    'contact.back': 'Tilbage til forsiden',
    'footer.follow': 'Følg med',
    'footer.newsletter': 'Få nye tekster på mail, cirka en gang om måneden.',
    'footer.emailLabel': 'E-mailadresse',
    'footer.subscribe': 'Tilmeld',
    'footer.rss': 'RSS-feed',
    'footer.write': 'Skriv til mig på',
    'footer.orForm': 'eller brug',
    'footer.form': 'kontaktformularen',
    'footer.follow2': 'Følg nye tekster via',
    'notfound.title': 'Denne side er gået videre',
    'notfound.body': 'Der er intet på denne adresse. Prøv forsiden eller arkivet.',
  },
} as const;

export type UIKey = keyof (typeof ui)['en'];
export const t = (lang: Lang, key: UIKey): string => ui[lang][key];

/** Build a localized path: url('da', 'writing', slug) → /da/writing/slug/ */
export const url = (lang: Lang, ...parts: string[]) =>
  '/' + [lang, ...parts].filter(Boolean).join('/') + '/';

const locales: Record<Lang, string> = { en: 'en-GB', da: 'da-DK' };

export const formatDate = (lang: Lang, date: Date, style: 'long' | 'short' = 'long') =>
  date.toLocaleDateString(locales[lang], {
    day: 'numeric',
    month: style === 'long' ? 'long' : 'short',
    year: 'numeric',
    timeZone: 'UTC',
  });

/** ISO date, used for <time datetime>. */
export const isoDate = (date: Date) => date.toISOString().slice(0, 10);

/** ISO 8601 week number, the way Danes date things ("uge 46"). */
export function isoWeek(date: Date) {
  const d = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  const day = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - day);
  const yearStart = Date.UTC(d.getUTCFullYear(), 0, 1);
  return { week: Math.ceil(((d.valueOf() - yearStart) / 86400000 + 1) / 7), year: d.getUTCFullYear() };
}

export const weekLabel = (lang: Lang, date: Date) => `${lang === 'da' ? 'Uge' : 'Week'} ${isoWeek(date).week}`;

/** "9–15 November" for the ISO week containing `date`. */
export function weekRange(lang: Lang, date: Date) {
  const d = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  const mon = new Date(d); mon.setUTCDate(d.getUTCDate() - ((d.getUTCDay() || 7) - 1));
  const sun = new Date(mon); sun.setUTCDate(mon.getUTCDate() + 6);
  const fmt = (x: Date, opts: Intl.DateTimeFormatOptions) => x.toLocaleDateString(locales[lang], { ...opts, timeZone: 'UTC' });
  const sameMonth = mon.getUTCMonth() === sun.getUTCMonth();
  const end = fmt(sun, { day: 'numeric', month: 'long' });
  const start = sameMonth ? fmt(mon, { day: 'numeric' }) : fmt(mon, { day: 'numeric', month: 'long' });
  return `${start}–${end}`;
}
