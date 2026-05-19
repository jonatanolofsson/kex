import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import AppCard from '../src/lib/components/AppCard.svelte';

function baseApp(overrides = {}) {
    return {
        name: 'demo',
        title: 'Demo',
        description: '',
        group: 'Other',
        icon: '✨',
        sync_status: 'Synced',
        health_status: 'Healthy',
        weight: 0,
        group_weight: 0,
        quick_links: [],
        ...overrides,
    };
}

describe('AppCard tooltip', () => {
    it('uses the full description as the card title (HTML hover tooltip)', () => {
        const longDescription =
            'A long-form description that gets truncated on the card itself ' +
            'but should remain accessible to operators on hover.';
        const { container } = render(AppCard, {
            props: { app: baseApp({ description: longDescription }) },
        });
        const card = container.querySelector('article.card');
        expect(card).toBeTruthy();
        expect(card.getAttribute('title')).toBe(longDescription);
    });

    it('falls back to the title when description is empty', () => {
        const { container } = render(AppCard, {
            props: { app: baseApp({ title: 'Demo title only' }) },
        });
        const card = container.querySelector('article.card');
        expect(card.getAttribute('title')).toBe('Demo title only');
    });

    it('the stretched link inside the card points at the detail page', () => {
        const { container } = render(AppCard, {
            props: { app: baseApp({ name: 'has spaces' }) },
        });
        const stretch = container.querySelector('a.stretch');
        expect(stretch).toBeTruthy();
        expect(stretch.getAttribute('href')).toBe('#/apps/has%20spaces');
    });
});

describe('AppCard quick-links', () => {
    it('renders no quick-link buttons when quick_links is empty', () => {
        const { container } = render(AppCard, { props: { app: baseApp() } });
        expect(container.querySelector('.quick-links')).toBeNull();
        expect(container.querySelectorAll('a.quick-link').length).toBe(0);
    });

    it('renders one quick-link when only app slot is set', () => {
        const { container } = render(AppCard, {
            props: {
                app: baseApp({
                    quick_links: [
                        { label: 'app', url: 'https://example/app', icon: '↗' },
                    ],
                }),
            },
        });
        const links = container.querySelectorAll('a.quick-link');
        expect(links.length).toBe(1);
        expect(links[0].getAttribute('href')).toBe('https://example/app');
        expect(links[0].getAttribute('target')).toBe('_blank');
        expect(links[0].getAttribute('rel')).toBe('noopener');
    });

    it('renders two quick-links in declared (app, docs) order', () => {
        const { container } = render(AppCard, {
            props: {
                app: baseApp({
                    quick_links: [
                        { label: 'app', url: 'https://example/app', icon: '↗' },
                        { label: 'docs', url: 'https://example/docs', icon: '📖' },
                    ],
                }),
            },
        });
        const links = [...container.querySelectorAll('a.quick-link')];
        expect(links.length).toBe(2);
        expect(links.map((a) => a.getAttribute('href'))).toEqual([
            'https://example/app',
            'https://example/docs',
        ]);
        // The aria-label embeds the slot label so screen-reader users can
        // distinguish the two buttons.
        expect(links[0].getAttribute('aria-label')).toContain('app');
        expect(links[1].getAttribute('aria-label')).toContain('docs');
    });

    it('drops entries with no url', () => {
        const { container } = render(AppCard, {
            props: {
                app: baseApp({
                    quick_links: [
                        { label: 'app', url: '', icon: '↗' },
                        { label: 'docs', url: 'https://example/docs', icon: '📖' },
                    ],
                }),
            },
        });
        const links = container.querySelectorAll('a.quick-link');
        expect(links.length).toBe(1);
        expect(links[0].getAttribute('href')).toBe('https://example/docs');
    });
});
