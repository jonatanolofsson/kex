import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
    // svelte.config.js wires `vitePreprocess` which breaks under vitest's
    // bundled Vite instance — override with an empty preprocessor since the
    // components only use plain CSS.
    plugins: [svelte({ hot: false, preprocess: [] })],
    // Svelte 5 ships separate server / client builds; the test renderer
    // needs the browser build to call `mount()`. Without this condition
    // we get `lifecycle_function_unavailable` at runtime.
    resolve: {
        conditions: ['browser'],
    },
    test: {
        environment: 'jsdom',
        globals: true,
        include: ['tests/**/*.test.js'],
    },
});
