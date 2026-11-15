# The character, page by page

How the Blender model is used on each page: the pose, the animation, the face, and the props that still need to be modelled. Motion follows [`ANIMATION.md`](ANIMATION.md). Faces are presets in `build.py` (`FACES`).

## Shared rules

- **One appearance per page.** He shows up once, in the page heading, plus at most one small moment further down: an empty state or an essay's end.
- **Size.** Hero about 320–440 px. Page heading about 180–300 px. Empty states about 120–170 px. He may spill over margins and into neighbouring content (see DESIGN.md).
- **How he's delivered.**
  - Animated placements use rendered sprite sheets played on a canvas, like the homepage (`HeroAvatar.astro`, `sheets.py`).
  - Still placements use one rendered WebP.
  - Every animated placement has a still fallback for reduced motion. When the footer's STOP is on, he shows his sleep pose.
- **Loops.** Idle loops are 2–4 s and start and end at rest. One-shot gestures (a wave, a sip, a cheer) play on arrival and when he's pointed at, then return to the idle.
- **Camera.** Three-quarter view turned toward the page's text (`--view -18`), the same lighting everywhere, and a transparent background with his soft shadow.
- **Faces available:**

  | Face | Eyes | Mouth | Fits |
  |---|---|---|---|
  | `smile` | open | smile | the default |
  | `happy` | upward arcs, a beaming squint | smile | waves, cheers, being pleased with something |
  | `content` | downward arcs, eyes softly shut | smile | listening, cosy moments, sleep |
  | `sip` | content | small "o" | drinking |
  | `wink` | one eye open, one happy | smile | looking closely, a little joke |
  | `muse` | open | small "o" | thinking, reading, curiosity |
  | `shout` | happy | big open "O" | cheering |
  | `surprised` | open | big open "O" | a surprise, like the 404 |

  Blinks: the open eye morphs to a mouth-thick bar and its socket closes with it. Every closed eye is a round-ended bar exactly as thick as the mouth, set in a matching groove.

## Pages

### Homepage (hero)
- **Pose and animation:** standing, `idle` loop (breathing, weight shift, a look at the viewer, one blink). `wave` plays on arrival and when pointed at. The `sleep` pose shows while motion is stopped.
- **Face:** `smile`. The wave could end on `happy` for a beat, which needs a crossfaded frame.
- **Props:** none.
- **Status:** built (this round).

### Blog (index)
- **Pose and animation:** sitting with a laptop, typing in short bursts with pauses. Head bobs slightly as he types and glances at the reader on a pause. Loop about 4 s.
- **Face:** `smile`, `muse` on pauses.
- **Props to model:**
  - **Laptop:** small, rounded, graphite, with a softly glowing screen and a `>_` prompt. Hinged lid as a separate object.

### Blog post (end of essay)
- **Pose and animation:** lying on his front, reading an open book. A still, or a slow page turn on a 6 s loop.
- **Face:** `content`.
- **Props to model:**
  - **Open book:** cloth cover in the section's indigo, cream pages, a soft spine curve, pages as one block plus a single turning page.

### Weeks
- **Pose and animation:** standing, holding a mug in both mittens (the attachments slid forward). Sips: lift, a `sip` face, a small exhale. Steam rises and curls in ink strokes. Loop about 5 s.
- **Face:** `smile`, then `sip`.
- **Props to model:**
  - **Mug:** speckled stoneware in warm off-white, chunky handle, coffee surface inside.
  - **Steam:** two or three ink-stroke curls as flat 2D shapes (the marks layer, so they recolour in dark mode).

### Projects (index)
- **Pose and animation:** standing at a small circuit board, soldering. Little dabs with the iron, a pause, a tiny puff of smoke, then he looks up pleased (`happy`). Loop about 5 s.
- **Face:** `muse` while working, `happy` on the look-up.
- **Props to model:**
  - **Soldering iron:** orange or yellow grip, steel tip, a curled cable.
  - **Circuit board:** green, gold pads, a couple of chunky components.
  - **Solder reel:** optional.
  - **Smoke puff:** ink-stroke marks.

### Project page
- **Pose and animation:** none in the heading; the project's images carry it. Optional small marks at the end: holding a screwdriver up (`happy`), or carrying a cardboard box when the project is "shipped".
- **Props to model:** screwdriver (orange grip, flat steel tip), cardboard box with tape.

### Photos
- **Pose and animation:** standing with a small rangefinder camera at his face, then a "click" (the camera nudges, three ink ticks flash). He lowers it and checks the screen (`muse`). Loop about 4 s.
- **Face:** `wink` while aiming, `muse` on the check.
- **Props to model:**
  - **Camera:** black and silver body with a lens barrel, tiny shutter button, strap optional.
  - **Ticks:** ink marks.

### My rotation
- **Pose and animation:** standing with headphones on, eyes shut, bobbing gently to a beat. The head nods on the beat, the body sways, one foot taps. Loop of 2 bars, about 4 s at 96 bpm.
- **Face:** `content`.
- **Props to model:**
  - **Headphones:** graphite cups with soft cushions and a thin band, fitted to his dome.
  - **Music notes:** optional, as ink marks.
- **Empty state:** carrying a stack of three books (indigo, brown, cream) that wobble as he walks in place. The books need modelling.

### About
- **Pose and animation:** standing, `wave` on a slow loop: wave, idle for about 4 s, wave again. Or a single wave on arrival, then `idle`.
- **Face:** `smile`, with `happy` at the top of the wave.
- **Props to model:** none.

### Contact
- **Pose and animation:** holding a d20, rolling it in his mittens. Tosses it up a little, catches it and looks at it (`muse`). Loop about 4 s.
- **Face:** `muse`, `happy` on the catch.
- **Props to model:**
  - **d20:** navy, crisp but slightly bevelled edges, cream numbers, with "20" facing the viewer.

### Message sent
- **Pose and animation:** a jump of joy (the `jump` move, with `shout` at the apex), or a lightbulb that lights above his raised mitten. Plays once, then idles.
- **Face:** `shout`, then `happy`.
- **Props to model:**
  - **Lightbulb:** glass with a warm emissive filament, a brass screw base, and ink rays.

### 404
- **Pose and animation:** sitting at a little retro terminal, typing, then turning to the viewer with a `surprised` face when the page loads. Loop: typing, then a glance at the screen.
- **Face:** `muse`, then `surprised`.
- **Props to model:**
  - **Terminal:** cream plastic box with a dark screen and a green `>_` prompt, plus a chunky keyboard.

### Empty lists
- **Pose and animation:** lounging in a beanbag, eyes shut, breathing slowly; the LED pulses faintly. Loop about 6 s.
- **Face:** `happy` (a satisfied squint, as in the reference) or `content`.
- **Props to model:**
  - **Beanbag:** warm brown fabric with soft folds. A sculpted mesh with a fabric shader.

### Header mark and favicon
- The flat drawing (`Avatar2D`) stays. It should be redrawn from a front render of the model so the two match: eye pills, mouth thickness and the LED and button positions.

## Props to model, in priority order

1. Mug + steam (Weeks)
2. Laptop (Blog)
3. Headphones (My rotation)
4. Soldering iron + circuit board + smoke (Projects)
5. Camera (Photos)
6. d20 (Contact)
7. Beanbag (empty lists)
8. Open book (essay end) and a stack of books (rotation, empty)
9. Retro terminal + keyboard (404)
10. Lightbulb (message sent)
11. Screwdriver, cardboard box (project pages, optional)

Each prop is one object (or a few), built in `build.py` like the others. It's parented to the mitten or body it belongs to, uses the same soft-touch materials, and keeps its proportions to him: chunky, rounded, a bit toy-like.

## Animation to build per page

| Page | Loop | One-shot |
|---|---|---|
| Home | `idle` | `wave` |
| Blog | `type` | `glance` |
| Essay end | `read` (page turn) | none |
| Weeks | `hold_mug` | `sip` |
| Projects | `solder` | `look_up` |
| Photos | `aim` | `click` |
| My rotation | `listen` (beat bob) | none |
| About | `idle` | `wave` |
| Contact | `roll_die` | `toss` |
| Message sent | `idle` | `jump` with a `shout` face |
| 404 | `type` | `surprised_turn` |
| Empty | `lounge` | none |

More ideas from the reference sheets, to use later:
- **Wizard with staff and cloak:** game-studies posts or D&D.
- **VR headset:** research on games or AI.
- **Campfire with a marshmallow:** a cosy weeknote.
- **Telescope or globe:** travel.
- **Holding a glowing cube:** AI/PhD posts.
- **Hammock:** holidays.
- **Astronaut:** sci-fi reading.
- **Knitting:** "making" posts.
- **Plant:** spring.
- **Scarf with falling leaves:** autumn weeks.
