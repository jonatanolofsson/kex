import { describe, it, expect, beforeEach } from 'vitest';
import { getTheme, setTheme, toggleTheme } from '../src/lib/theme.js';

describe('theme persistence', () => {
    beforeEach(() => {
        localStorage.clear();
        document.documentElement.removeAttribute('data-theme');
    });

    it('defaults to mocha when no preference is stored', () => {
        expect(getTheme()).toBe('mocha');
    });

    it('persists setTheme to localStorage', () => {
        setTheme('latte');
        expect(getTheme()).toBe('latte');
        expect(document.documentElement.getAttribute('data-theme')).toBe('latte');
    });

    it('toggle flips mocha <-> latte', () => {
        setTheme('mocha');
        toggleTheme();
        expect(getTheme()).toBe('latte');
        toggleTheme();
        expect(getTheme()).toBe('mocha');
    });
});
