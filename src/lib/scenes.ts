/**
 * Which rendered 3D scene (design/avatar/scenes.py, packed into public/avatar/scenes/) plays for a
 * pose. A pose without a rendered scene keeps its cut-out.
 */
const metas = import.meta.glob<{ ratio: number }>('../../public/avatar/scenes/*/meta.json', { eager: true, import: 'default' });

const POSE_TO_SCENE: Record<string, string> = {
  solder: 'projects', laptop: 'blog', coffee: 'weeks', camera: 'photos', headphones: 'rotation',
  d20: 'contact', idea: 'sent', terminal: '404', beanbag: 'empty', books: 'rotation_empty',
  'lie-read': 'essay', wave: 'about',
};

export function sceneFor(pose: string | undefined): { scene: string; ratio: number } | undefined {
  const scene = pose && POSE_TO_SCENE[pose];
  const meta = scene && metas[`../../public/avatar/scenes/${scene}/meta.json`];
  return scene && meta ? { scene, ratio: meta.ratio } : undefined;
}
