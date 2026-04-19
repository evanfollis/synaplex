// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import tailwind from '@astrojs/tailwind';

// Canonical site URL. Override at build time with ASTRO_SITE env var once
// the custom domain is registered; pages.dev URL is fine for the first deploy.
const site = process.env.ASTRO_SITE || 'https://agentstack.pages.dev';

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
