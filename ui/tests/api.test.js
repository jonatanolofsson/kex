import { describe, it, expect, beforeEach, vi } from 'vitest';
import { listApps, getApp } from '../src/lib/api.js';

describe('api wrappers', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it('listApps GETs /api/apps', async () => {
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => [{ name: 'a' }],
        });
        const rows = await listApps();
        expect(rows).toEqual([{ name: 'a' }]);
        expect(global.fetch).toHaveBeenCalledWith(
            '/api/apps',
            expect.objectContaining({ headers: { Accept: 'application/json' } }),
        );
    });

    it('getApp encodes the name', async () => {
        global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
        await getApp('weird name');
        expect(global.fetch).toHaveBeenCalledWith(
            '/api/apps/weird%20name',
            expect.any(Object),
        );
    });

    it('throws with status on non-2xx', async () => {
        global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 404 });
        await expect(getApp('missing')).rejects.toMatchObject({ status: 404 });
    });
});
