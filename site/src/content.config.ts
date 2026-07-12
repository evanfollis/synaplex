import { defineCollection } from 'astro:content';

// These publication surfaces are intentionally empty today. Declaring them
// makes that state explicit and avoids Astro's deprecated folder auto-discovery.
const emptyCollection = () => defineCollection({
  loader: async () => [],
});

export const collections = {
  editorial: emptyCollection(),
  lab: emptyCollection(),
  directory: emptyCollection(),
};
