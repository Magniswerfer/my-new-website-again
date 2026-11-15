# Animating the character

Every animation of him should feel like a Pixar short: soft, weighted, readable and warm. He is small, plump, a bit careful, curious, and happiest when he is making something. He is a moulded plastic thing that is alive, not a rubber toy and not a robot that whirrs. These rules apply to every move, on the site and anywhere else.

The rig and the moves are built by [`build.py`](build.py). Run it with `--anim <move>` to render one. [`DESIGN.md`](../DESIGN.md#avatar) says where he appears.

## Who he is when he moves

- **Gentle, not hyper.** He saves energy. Big moves are rare and earned, like a hello, a jump of joy or a surprise.
- **Curious.** His head leads. He looks at things before his body turns to them.
- **Careful hands.** He reaches deliberately, holds things with both mittens, and settles before letting go.
- **Weighty for his size.** He is short and dense. He sinks into landings and takes a beat to push off.
- **Never mechanical.** No linear moves, no perfectly symmetric poses, no instant stops. The LED is his only "electronic" tell.

## The principles, applied to him

1. **Squash and stretch.** The shell squashes and stretches as one piece, and always keeps its volume: the sides widen by 1/√k when the height goes by k. Typical amounts:
   - breathing: 1–1.5 %
   - walking: about 2.5 %
   - crouch and landing: 10–12 %
   - launch and fall: about 10 %

   The ribs stay firm and the dome stays round. Limbs squash 3–5 % on contact and widen to keep their volume. The face never distorts. It rides on the head.
2. **Anticipation.** Every action starts with a small move the other way. He dips before a wave, sinks into a crouch before a jump, and shifts his weight before a step. For bigger actions he holds the anticipation briefly, as a moving hold.
3. **Staging.** One idea at a time, readable in silhouette. Keep the arms clear of the body on the important beat, and keep the face turned toward the viewer on emotional beats.
4. **Straight ahead and pose to pose.** Moves are blocked on key poses first (contact, down, passing, up; crouch, launch, apex, land). Then they are eased between the poses. Planted feet are solved in world space so they never slide.
5. **Follow-through and overlapping action.** Nothing stops at once. The arms trail the body by 1–2 frames, and the head drags behind the shell, then catches up and overshoots. One arm runs a frame behind the other. Every gesture ends with a small overshoot and settle.
6. **Slow in and slow out.** Every pose eases in and out. Only contacts are sharp, like a foot landing or a blink closing.
7. **Arcs.** Hands, feet and the top of the dome travel on arcs, never in straight lines. Mitten tips swing from the shoulder. Feet lift in a low arc.
8. **Secondary action.** Breathing, blinks, the head tilting, arms drifting, feet tucking in the air. These support the main action and never compete with it.
9. **Timing.** 24 fps. Fewer frames feel lighter and quicker; more feel heavier and calmer. He sits on the calm side. Starting points:

   | Move | Timing at 24 fps |
   |---|---|
   | Walk | 28 frames per left and right step |
   | Wave | dip 4, raise 8, arcs 24–32, settle 10–12 |
   | Jump | about 48 frames from rest to rest |
   | Blink | close in 2 frames, open in 4 |
   | Idle | 4 s loop |
10. **Exaggeration.** Push just past real, then pull back. A Pixar touch, not a cartoon smear. He never breaks, bends at hard angles or loses his silhouette.
11. **Solid drawing.** He is a solid object with real volume. Check every move from the front (weight shift) and the side (ground contact). Feet never sink below the floor or slide while planted. The shoulder and hip roots stay tucked into the shell.
12. **Appeal.** Soft, round, slightly asymmetric poses. A small head tilt, one arm a little ahead of the other. The smile is constant. Emotion comes from the body, head and eyes.

## How his parts move

- **Body.** The body control pivots low inside the shell, just above the hips. It leans, shifts toward the foot carrying the weight, bobs, and squashes and stretches.
- **Neck.** The head bone pivots just above the ribs and carries the dome, eyes, mouth, LED and button. It leads into turns and looks. It steadies against the body's sway, drags on fast moves, and nods on landings. Keep it within about ±10° for most moves.
- **Hip.** The hips bone pivots at the bottom of the ribs and carries the base and the leg attachments. It turns toward the stepping leg and tucks under in crouches.
- **Arms.** Each arm has an attachment that travels round the shell, forward to hold things and back at rest, plus a shoulder that swings. Two bones give a soft bend. A squash key handles contact.
- **Legs.** Each leg has a hip attachment that slides along the underside and a foot control that stays planted. The leg leans toward its foot rather than shearing. A squash key carries the weight.
- **Eyes.** Blinks squash the eye pills closed and open again. He blinks every 3–6 s, and always on a big change of direction.
- **LED.** On while awake, grey and dark while asleep. It may fade, never flash.

## Moves that exist

| Move | Frames | What it does |
|---|---|---|
| `idle` | 96 (loops) | Breathes twice, shifts his weight, looks toward the viewer with a moving hold, tilts his head, blinks once. Starts and ends at rest. |
| `wave` | 64 | Dips, raises the left arm beside his head, three shrinking arcs, settles. Head tilts toward the arm. |
| `walk` | 28 (loops) | Travelling walk: contact, down, passing, up. Feet fixed while planted. |
| `walk_start` / `walk_stop` | 20 / 26 | Weight shift into the first step; a short last step, dip and settle. |
| `turn` | 36 | 90° left in two steps, head leading. |
| `jump` | 48 | Counter-rise, crouch with a moving hold, stretch, apex tuck, feet land first, dip, overshoot, settle. |
| `reach` | 64 | Shoulders slide forward, arms curve round an object, slight lean in, contact squash, return. |
| `sit`, `sleep` | poses | Legs out in front; eyes closed, LED off, slight forward slump. |

## Checklist before a move ships

- [ ] It starts and ends at rest, or loops seamlessly.
- [ ] There is anticipation before the main action and a settle after it.
- [ ] Nothing moves linearly, and nothing stops dead.
- [ ] Arms and head overlap the body by a frame or two.
- [ ] The shell keeps its volume, and the ribs and dome stay firm.
- [ ] From the front: the weight is over the supporting foot.
- [ ] From the side: no foot slides or dips below the floor. (`build.py` checks this: every move currently passes with zero slide.)
- [ ] It reads in silhouette and at thumbnail size.
- [ ] It feels like him: gentle, curious, careful, a little proud of himself.
