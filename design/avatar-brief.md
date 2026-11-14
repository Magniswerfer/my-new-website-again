# Avatar brief: a small character for Magnus

For generating images with ChatGPT (or another image model). Copy the **prompt** sections as they are; the rest is
context for you.

## What it's for

A small mascot-style character that stands in for Magnus on magnushkaspersen.com: next to his name, on the About page,
and as a friendly sign-off. It has to work tiny (32–48px next to the name) and medium (200–300px on About).

## The site it lives on

A personal site designed like a late-80s/early-90s **Frog Design** or Braun object: a warm off-white "snow white" body
with fine horizontal grooves, pill-shaped hardware keys with small green LEDs, and small engraved uppercase labels.
Each section has a natural-dye colour. Fine flowing threads in those colours run across the page.

### Colours (use these exactly)

| Name | Hex | Use on the character |
|---|---|---|
| Snow white | `#EDECE7` | Main body colour |
| Key light | `#FAF9F5` | Highlights, the top of rounded surfaces |
| Key shadow | `#DCDAD3` | Soft shading on the body |
| Graphite | `#1D1D1F` | Eyes, fine outlines, small details |
| LED green | `#2FB352` | One small glowing light (the "on" indicator) |
| Indigo | `#2E4D8F` | Accent (blog) |
| Madder red | `#B4412F` | Accent (weeks) |
| Weld yellow | `#C9962A` | Accent (projects) |
| Moss green | `#4F7B52` | Accent (photos) |
| Plum | `#6E4A6E` | Accent (my rotation) |
| Walnut | `#6A5242` | Accent (about) |

Use at most two of the six accents on the character itself. The rest can appear as a few loose coloured threads.

## Who the character is

Magnus is 32 and lives in Aarhus, Denmark. He's a maker and tinkerer who builds things, solders electronics, fixes what's
broken at home and writes small open-source tools. He reads a lot of fantasy and sci-fi, loves video games and studies
them, and has a PhD in AI in education. He's warm, curious, a bit nerdy and quietly playful.

The character shouldn't be a portrait. It should feel like a small, friendly **object with a personality**, the way Frog
Design gave products character ("form follows emotion"), and the way modern AI companies give their assistants simple,
warm mascot characters: soft, rounded, a little abstract, instantly readable, expressive with very few features. Think
of Meta's Muse character as one point of reference for the level of simplicity and charm.

### Design direction

- **Shape:** a compact, rounded body like a small piece of hardware: a soft pill or rounded-rectangle shape that could
  be a pocket device, a key or a little robot. Chunky and friendly, never sharp.
- **Face:** very minimal. Two small graphite eyes (dots or short ovals), optionally a tiny smile. No nose, no detailed
  features.
- **Hardware details (pick two or three):** fine horizontal grooves across the lower body; one small pill-shaped key on
  its front; a tiny green LED that's lit (it's "on"); a small engraved label such as "MHK".
- **Something of Magnus (pick one or two, keep them tiny):** a loose coloured thread it's holding or that trails from
  it; a small screwdriver or soldering iron; a tiny open book; a little game controller.
- **Material:** matte snow-white plastic with soft shading, like a well-made product photo. Not glossy, not metallic.
- **Mood:** playful, curious, helpful. A slight head tilt or a small wave is good.
- **Avoid:** realistic human faces, anime style, heavy outlines, gradients outside the palette, text other than "MHK",
  busy backgrounds, logos of real companies.

## Prompts

### Prompt 1: the main character

> A small, friendly mascot character for a personal website, designed in the spirit of 1980s Frog Design and Braun
> hardware: a compact rounded pill-shaped body in matte snow-white plastic (#EDECE7) with soft shading (#DCDAD3) and
> highlights (#FAF9F5). Fine horizontal grooves are cut across its lower body. On its front is one small pill-shaped
> key and a tiny glowing green LED (#2FB352) that is switched on. Its face is minimal: two small graphite (#1D1D1F)
> oval eyes and a tiny smile. It holds a single fine indigo thread (#2E4D8F) that curls away from it in a soft
> flowing line, with a weld-yellow thread (#C9962A) beside it. Friendly, curious and quietly playful, with a slight
> head tilt. Clean product-render look, soft studio light, centred, plain off-white background (#EDECE7), no text
> except a tiny engraved "MHK" on its side. Simple enough to read at 40 pixels.

### Prompt 2: variations

> Using the same character, make a sheet of six small poses on a plain #EDECE7 background, evenly spaced: waving;
> holding a tiny screwdriver; reading a tiny open book; holding a tiny game controller; with its green LED off and eyes
> closed (sleeping); and looking up curiously. Keep the same shape, colours, grooves and LED in every pose.

### Prompt 3: icon version

> The same character as a flat icon for 48×48 pixels: the snow-white pill body, two graphite eyes, the green LED and a
> few grooves, drawn flat with one level of shading. No thread, no background (transparent).

## Delivery

- **Format:** PNG with a transparent background (or a clean `#EDECE7` background I can remove), at least 1024×1024.
- **Versions needed:** the main character; the icon version; the pose sheet (optional).
- **Dark mode:** the site also has a dark theme (`#1A1B1E` background). The snow-white character should still read
  well on it; if not, make a version with a slightly darker body (`#3B3D41`) and the same LED and accents.

Once you have images, add them to `src/assets/` (or send them to Claude) and they can be placed next to the name and on
the About page.
