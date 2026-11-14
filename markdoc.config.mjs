import { defineMarkdocConfig, component } from '@astrojs/markdoc/config';

export default defineMarkdocConfig({
  tags: {
    // {% sidenote note="The note text." %}words it belongs to{% /sidenote %}
    sidenote: {
      render: component('./src/components/Sidenote.astro'),
      attributes: { note: { type: String, required: true } },
    },
  },
});
