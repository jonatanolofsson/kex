/* Theme persistence + toggle. Two themes: 'mocha' (dark) and 'latte' (light).
   Stored under localStorage.kex.theme; default 'mocha'. */

const KEY = 'kex.theme';
const DEFAULT = 'mocha';

export function getTheme() {
    try {
        return localStorage.getItem(KEY) || DEFAULT;
    } catch {
        return DEFAULT;
    }
}

export function setTheme(theme) {
    try {
        localStorage.setItem(KEY, theme);
    } catch {
        /* ignore */
    }
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme === 'latte' ? 'light' : 'dark';
}

export function toggleTheme() {
    setTheme(getTheme() === 'mocha' ? 'latte' : 'mocha');
}

export function initTheme() {
    setTheme(getTheme());
}
