import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import AppCard from '../src/lib/components/AppCard.svelte';

describe('AppCard tooltip', () => {
    it('uses the full description as the link title (HTML hover tooltip)', () => {
        const longDescription =
            'A long-form description that gets truncated on the card itself ' +
            'but should remain accessible to operators on hover.';
        const { container } = render(AppCard, {
            props: {
                app: {
                    name: 'demo',
                    title: 'Demo',
                    description: longDescription,
                    group: 'Other',
                    icon: '✨',
                    sync_status: 'Synced',
                    health_status: 'Healthy',
                    weight: 0,
                },
            },
        });
        const anchor = container.querySelector('a.card');
        expect(anchor).toBeTruthy();
        expect(anchor.getAttribute('title')).toBe(longDescription);
    });

    it('falls back to the title when description is empty', () => {
        const { container } = render(AppCard, {
            props: {
                app: {
                    name: 'demo',
                    title: 'Demo title only',
                    description: '',
                    group: 'Other',
                    icon: null,
                    sync_status: null,
                    health_status: null,
                    weight: 0,
                },
            },
        });
        const anchor = container.querySelector('a.card');
        expect(anchor.getAttribute('title')).toBe('Demo title only');
    });
});
