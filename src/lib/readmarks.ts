/**
 * Read marks: remember, in this browser only, which posts and weeks a
 * visitor has already seen, so their rows get a pencil tick next time.
 * Storage can be unavailable (private mode, blocked); then nothing happens.
 */
const READ = 'mhk:read';
const SEEN_WEEKS = 'mhk:weeks-seen';

function load(key: string): Set<string> {
  try { return new Set(JSON.parse(localStorage.getItem(key) ?? '[]')); } catch { return new Set(); }
}
function save(key: string, set: Set<string>) {
  try { localStorage.setItem(key, JSON.stringify([...set].slice(-500))); } catch {}
}

const norm = (path: string) => (path.endsWith('/') ? path : path + '/');

/** Call on a post page: remember that it has been read. */
export function markRead(path = location.pathname) {
  const read = load(READ);
  read.add(norm(path));
  save(READ, read);
}

/** Tick list rows ([data-href]) whose post has been read. */
export function tickRead(root: ParentNode = document) {
  const read = load(READ);
  root.querySelectorAll<HTMLElement>('[data-href]').forEach((row) => {
    if (read.has(norm(row.dataset.href!))) row.dataset.read = '';
  });
}

/** On the Weeks page: tick weeks seen on an earlier visit, then remember all of them. */
export function tickWeeks(root: ParentNode = document) {
  const seen = load(SEEN_WEEKS);
  const rows = root.querySelectorAll<HTMLElement>('[data-week]');
  rows.forEach((row) => { if (seen.has(row.dataset.week!)) row.dataset.read = ''; });
  rows.forEach((row) => seen.add(row.dataset.week!));
  save(SEEN_WEEKS, seen);
}
