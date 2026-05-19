import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getConfig } from '../src/lib/api.js';

describe('getConfig API wrapper', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it('GETs /api/config and returns the parsed body', async () => {
        const fakeBody = {
            cluster_name: 'EdgeLab',
            hero_tagline: 'Welcome.',
            header_links: [
                { label: 'Docs', url: 'https://docs.example', icon: 'book' },
            ],
            welcome_html: '<p>Hi</p>',
        };
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => fakeBody,
        });
        const result = await getConfig();
        expect(result).toEqual(fakeBody);
        expect(global.fetch).toHaveBeenCalledWith(
            '/api/config',
            expect.objectContaining({ headers: { Accept: 'application/json' } }),
        );
    });

    it('throws with .status on non-2xx', async () => {
        global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 503 });
        await expect(getConfig()).rejects.toMatchObject({ status: 503 });
    });
});
