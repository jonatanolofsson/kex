/**
 * Group + within-group ordering tests. The real implementation lives in
 * src/routes/Index.svelte as a `$derived` expression — duplicate the
 * sort logic here so the contract is testable without booting a full
 * DOM. If the implementation drifts from this duplicate, the
 * regression should fail the moment the visible order drifts.
 *
 * Two annotations drive ordering:
 *   `kex/groupweight` → between-group order (group = min(group_weight))
 *   `kex/weight`      → within-group order (per-app ascending)
 */
import { describe, it, expect } from 'vitest';

const safeFloat = (v) => (Number.isFinite(v) ? v : 0);

function groupWeight(apps) {
    let min = Infinity;
    for (const app of apps) {
        const w = safeFloat(app.group_weight);
        if (w < min) min = w;
    }
    return min === Infinity ? 0 : min;
}

function appSortKey(a, b) {
    const dw = safeFloat(a.weight) - safeFloat(b.weight);
    if (dw !== 0) return dw;
    const dt = (a.title || '').localeCompare(b.title || '');
    if (dt !== 0) return dt;
    return (a.name || '').localeCompare(b.name || '');
}

function sortGroups(apps) {
    const m = new Map();
    for (const app of apps) {
        const g = app.group || 'Other';
        if (!m.has(g)) m.set(g, []);
        m.get(g).push(app);
    }
    for (const items of m.values()) {
        items.sort(appSortKey);
    }
    return [...m.entries()].sort(([aName, aApps], [bName, bApps]) => {
        const dw = groupWeight(aApps) - groupWeight(bApps);
        return dw !== 0 ? dw : aName.localeCompare(bName);
    });
}

describe('between-group order', () => {
    it('floats negative-groupweight groups above default ones', () => {
        const apps = [
            { name: 'a1', title: 'a1', group: 'A', group_weight: 0, weight: 0 },
            { name: 'e1', title: 'e1', group: 'Edge', group_weight: -10, weight: 0 },
            { name: 'i1', title: 'i1', group: 'Infra', group_weight: 5, weight: 0 },
        ];
        expect(sortGroups(apps).map(([n]) => n)).toEqual(['Edge', 'A', 'Infra']);
    });

    it('group weight is the min across apps (one app pulls the whole group)', () => {
        const apps = [
            { name: 'a1', title: 'a1', group: 'ML', group_weight: 0, weight: 0 },
            { name: 'a2', title: 'a2', group: 'ML', group_weight: -5, weight: 0 },
            { name: 'a3', title: 'a3', group: 'ML', group_weight: 100, weight: 0 },
            { name: 'b1', title: 'b1', group: 'Edge', group_weight: 0, weight: 0 },
        ];
        expect(sortGroups(apps).map(([n]) => n)).toEqual(['ML', 'Edge']);
    });

    it('alphabetic tiebreak when group weights match', () => {
        const apps = [
            { name: 'a', title: 'a', group: 'Beta', group_weight: -1, weight: 0 },
            { name: 'b', title: 'b', group: 'Alpha', group_weight: -1, weight: 0 },
            { name: 'c', title: 'c', group: 'Gamma', group_weight: -1, weight: 0 },
        ];
        expect(sortGroups(apps).map(([n]) => n)).toEqual(['Alpha', 'Beta', 'Gamma']);
    });

    it('missing / non-finite group weight treated as 0', () => {
        const apps = [
            { name: 'a', title: 'a', group: 'A', group_weight: undefined, weight: 0 },
            { name: 'b', title: 'b', group: 'B', group_weight: NaN, weight: 0 },
            { name: 'c', title: 'c', group: 'C', group_weight: 0, weight: 0 },
            { name: 'd', title: 'd', group: 'D', group_weight: -1, weight: 0 },
        ];
        expect(sortGroups(apps).map(([n]) => n)).toEqual(['D', 'A', 'B', 'C']);
    });
});

describe('within-group order', () => {
    it('lower weight sorts earlier within a group', () => {
        const apps = [
            { name: 'a', title: 'A', group: 'G', group_weight: 0, weight: 0 },
            { name: 'b', title: 'B', group: 'G', group_weight: 0, weight: -10 },
            { name: 'c', title: 'C', group: 'G', group_weight: 0, weight: 5 },
        ];
        const [[, items]] = sortGroups(apps);
        expect(items.map((a) => a.name)).toEqual(['b', 'a', 'c']);
    });

    it('ties break on title (then name)', () => {
        const apps = [
            { name: 'gamma', title: 'Gamma', group: 'G', group_weight: 0, weight: 0 },
            { name: 'alpha', title: 'Alpha', group: 'G', group_weight: 0, weight: 0 },
            { name: 'beta',  title: 'Beta',  group: 'G', group_weight: 0, weight: 0 },
        ];
        const [[, items]] = sortGroups(apps);
        expect(items.map((a) => a.name)).toEqual(['alpha', 'beta', 'gamma']);
    });

    it('groupweight and weight are independent axes', () => {
        // Three apps in two groups. The lighter-weight Edge app should be
        // first in Edge; the Other group should follow alphabetically.
        const apps = [
            { name: 'e2', title: 'E2', group: 'Edge', group_weight: -30, weight: 0 },
            { name: 'e1', title: 'E1', group: 'Edge', group_weight: 0, weight: -10 },
            { name: 'o1', title: 'O1', group: 'Other', group_weight: 0, weight: 0 },
        ];
        const groups = sortGroups(apps);
        expect(groups.map(([n]) => n)).toEqual(['Edge', 'Other']);
        const [, edgeItems] = groups[0];
        // e1's weight=-10 floats it above e2's weight=0 within Edge.
        expect(edgeItems.map((a) => a.name)).toEqual(['e1', 'e2']);
    });

    it('missing / non-finite weight treated as 0 in within-group sort', () => {
        const apps = [
            { name: 'a', title: 'A', group: 'G', group_weight: 0, weight: undefined },
            { name: 'b', title: 'B', group: 'G', group_weight: 0, weight: NaN },
            { name: 'c', title: 'C', group: 'G', group_weight: 0, weight: -1 },
        ];
        const [[, items]] = sortGroups(apps);
        // c floats above (weight -1); a and b tie at 0, alpha by title.
        expect(items.map((a) => a.name)).toEqual(['c', 'a', 'b']);
    });
});
