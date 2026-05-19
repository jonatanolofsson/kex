/* Module-level UI config store, hydrated once by App.svelte on mount.
 *
 * No external store library; a Svelte 5 rune-backed object is enough.
 * Routes import { config } and read the reactive fields directly.
 */

import { getConfig } from './api.js';

const EMPTY = {
    cluster_name: '',
    hero_tagline: '',
    header_links: [],
    welcome_html: '',
};

export const config = $state({ ...EMPTY });

let hydrated = false;

/** Fetch /api/config once per page load and merge into the store. */
export async function hydrateConfig() {
    if (hydrated) return;
    hydrated = true;
    try {
        const fresh = await getConfig();
        Object.assign(config, EMPTY, fresh);
    } catch (e) {
        // Backend down or config route missing — fall back to empties so the
        // UI still renders. Logged for surface visibility.
        // eslint-disable-next-line no-console
        console.warn('kex: failed to hydrate /api/config; using empty defaults', e);
    }
}
