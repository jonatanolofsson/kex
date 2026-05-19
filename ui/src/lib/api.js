/* Thin fetch wrappers around the FastAPI backend. Centralised here so
   the rest of the UI stays free of URL strings, and tests can mock
   one place if needed. */

const API_BASE = '/api';

async function _get(path) {
    const response = await fetch(`${API_BASE}${path}`, {
        headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
        const error = new Error(`HTTP ${response.status}`);
        error.status = response.status;
        throw error;
    }
    return response.json();
}

/** Card-shaped row per kex-enabled Application. */
export async function listApps() {
    return _get('/apps');
}

/** Full detail view for one Application by name. */
export async function getApp(name) {
    return _get(`/apps/${encodeURIComponent(name)}`);
}

/** Cluster-scoped UI config (header links, welcome, cluster name, tagline). */
export async function getConfig() {
    return _get('/config');
}
