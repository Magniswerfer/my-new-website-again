# magnushkaspersen.com design system

The visual system for the site, agreed in November 2026. The working reference is
[`homepage-prototype.html`](homepage-prototype.html) (open it in a browser). The site's tokens live
in `src/styles/global.css` and follow this document. Why the site looks like this is in
[`PROFILE.md`](../PROFILE.md), under "The person behind it".

## The idea in one line

**Frog hardware with living threads.** The fixed parts of the page are built like a piece of late-Braun or early-Frog
hardware: a snow-white body, horizontal grooves, pill keys sunk into a recess, small engraved labels and a green LED.
The living parts are drawn with fine dyed threads that flow and grow as content is added.

## Principles

1. **Hardware for what stays, threads for what grows.** Navigation, controls and labels are hardware. Content and its
   growth are threads.
2. **Honest.** The threads are generated from the real content: each section has its own dye, and the more a section
   holds, the more of its threads there are. Nothing on the page explains this; it simply grows.
3. **One loud thing per page.** The headline. Everything else is quiet.
4. **Input gets a response, rest is calm.** Keys press, LEDs light, links underline. The only motion that isn't a
   response to the visitor is the slow drift of the threads, and the visitor can stop it.
5. **Only horizontal lines.** Grooves and rules are horizontal. No vertical stripes, no boxes around content.
6. **Edge to edge.** Threads run to both edges of the window, without margins.

## Colour

Snow-white body, near-black ink, one green for LEDs, and a natural-dye colour per section. Colour is used for icons,
threads and the active state, never for large surfaces.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--body` | `#EDECE7` | `#1A1B1E` | Page background (snow white) |
| `--ink` | `#1D1D1F` | `#ECEAE4` | Text |
| `--soft` | `#5F5D58` | `#A6A39C` | Secondary text |
| `--engrave` | `#8B8880` | `#77746E` | Engraved labels |
| `--groove` | ink at 7.5% | white at 5% | Fine grooves |
| `--groove-strong` | ink at 16% | white at 10% | Footer grooves |
| `--led` | `#2FB352` | `#45D06A` | Lit LED (current page, playing, open) |
| `--led-off` | `#B9B7B0` | `#2A322C` | Unlit LED |
| `--key-top` / `--key-bottom` | `#FAF9F5` / `#DCDAD3` | `#3B3D41` / `#2C2E31` | Pill key surface |
| `--key-edge` | `#B3B0A8` | `#141517` | Key side wall |
| `--recess-strip` | `#D6D4CD` | `#111214` | Recess the keys sit in |

### Section dyes

Each section keeps its colour everywhere: its icon, its threads and its links.

| Section | Token | Light | Dark |
|---|---|---|---|
| Blog | `--blog` | `#2E4D8F` indigo | `#7E9BE0` |
| Weeks | `--weeks` | `#B4412F` madder | `#E2735F` |
| Projects | `--projects` | `#C9962A` weld | `#E3B653` |
| Photos | `--photos` | `#4F7B52` moss | `#84B585` |
| My rotation | `--rotation` | `#6E4A6E` plum | `#B98BB9` |
| About | `--about` | `#6A5242` walnut | `#C29F86` |

On a section's own pages, `--accent` is that section's dye.

## Type

One family: **Instrument Sans** (variable weight and width), self-hosted.

| Role | Style |
|---|---|
| Headline (one per page) | 600, `clamp(44px, 6.4vw, 80px)`, line-height 1, letter-spacing −0.03em |
| Lede | 400, `clamp(19px, 2vw, 23px)`, line-height 1.4 |
| Item title | 600, 22px, letter-spacing −0.01em |
| Section heading | 600, 17px, with the section's icon |
| Body | 400, 16.5px, line-height 1.55 |
| Engraved label | 600, 11px, uppercase, letter-spacing 0.14em, width 90%, `--engrave` |
| Key label | 600, 11px (10px small), uppercase, letter-spacing 0.12em, width 90% |

Engraved labels are for small facts printed on the "hardware": the week line, web addresses, "Contact", "Motion".
Never for headings.

## Icons

One line-icon set on a 24-unit grid: 1.75 stroke, round caps and joins, always drawn in the section's dye. Blog is a
pen, Weeks a calendar with one marked day, Projects a wrench, Photos a camera, My rotation a disc, About a person.

## Components

### Key
A pill-shaped key cap sunk into a recess, like the Walkman's PLAY and STOP. It's built like real hardware: a light,
slightly dished top with a highlight along its upper edge, a 3px side wall underneath (`--key-edge`), and a soft drop
shadow. Pointing at it lowers it 1px; pressing it travels 3px so the side wall disappears into the body. A key that is
switched on (the current page, PLAY while playing) stays pressed in. A key can carry an **LED**: a 6–8px dot, unlit
(`--led-off`) or lit (`--led` with a soft glow).

### Menu
- **Desktop:** the section keys in a single row inside a rounded recessed strip, each with its icon and an LED.
  The current page's LED is lit. "Dansk"/"English" sits at the end as plain text.
- **Phone:** a MENU key (with LED) in the top bar. It opens a full-page sheet in the page colour, with one key per row.
  The key then reads CLOSE and its LED is lit, and the page behind doesn't scroll.

### Grooves
Fine horizontal lines cut into a surface. The footer's grooves fade in from the top, so the first lines are almost
invisible.

### Contour field (homepage only)
The hero: a field of about 84 fine lines that gather into strands and fan out again, like combed fibre. A few lines
are dyed in each section's colour. It starts behind the header and runs through the hero, edge to edge, and fades out
under the headline so the text stays clear. It appears on the homepage only.

### Section threads
Behind each homepage section, a soft band of threads in that section's dye drifts across the page, fading in from the
left. The more the section holds, the wider the band. Sections are separated by space, not lines. On every other page,
one band in that page's own dye runs behind the page heading.

### Footer
Contact sentences on plain grooves that fade in from the top. Below, two small keys (PLAY and STOP) under the engraved label "Motion".

### Avatar
A small character stands in for Magnus. The brief for generating it is in [`avatar-brief.md`](avatar-brief.md).

## Motion

- Threads drift slowly, at about a tenth of a cycle per second. Nothing else moves on its own.
- PLAY/STOP in the footer starts and stops the drift, and the choice is remembered.
- With reduced motion turned on, the threads are drawn once and stay still.
- Kept from earlier rounds: the reading line on essays.

## Layout

- Max content width 1180px, side gutter at least 28px.
- Section grid: a 14rem label column and a content column of at most 40rem. On phones, one column.
- Everything is left-aligned.
