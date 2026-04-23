// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import tailwind from '@astrojs/tailwind';

// Canonical site URL. Production deploy target is synaplex.ai (apex).
// Override at build time with ASTRO_SITE env var for staging previews.
// The CF zone for synaplex.ai is already provisioned.
const site = process.env.ASTRO_SITE || 'https://synaplex.ai';

export default defineConfig({
  site,
  integrations: [
    mdx(),
    sitemap(),
    tailwind({ applyBaseStyles: false }),
  ],
  build: {
    format: 'directory',
  },
});
