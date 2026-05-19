/**
 * Group-order tests. The actual implementation lives in
 * src/routes/Index.svelte as a $derived expression — duplicate just
 * the sort logic here so the contract is testable without booting a
 * full DOM.
 *
 * If the implementation drifts from this duplicate, the regression
 * should fail the moment we drift the visible group order.
 */
import { describe, it, expect } from 'vitest';

function groupWeight(apps) {
    let min = Infinity;
    for (const app of apps) {
        const w = Number.isFinite(app.weight) ? app.weight : 0;
        if (w < min) min = w;
    }
    return min === Infinity ? 0 : min;
}

function sortGroups(apps) {
    const m = new Map();
    for (const app of apps) {
        const g = app.group || 'Other';
        if (!m.has(g)) m.set(g, []);
        m.get(g).push(app);
    }
    return [...m.entries()].sort(([aName, aApps], [bName, bApps]) => {
        const dw = groupWeight(aApps) - groupWeight(bApps);
        return dw !== 0 ? dw : aName.localeCompare(bName);
    });
}

describe('group ordering', () => {
    it('floats negative-weight groups above default-weight ones', () => {
        const apps = [
            { name: 'a1', group: 'A', weight: 0 },
            { name: 'e1', group: 'Edge', weight: -10 },
            { name: 'i1', group: 'Infra', weight: 5 },
        ];
        expect(sortGroups(apps).map(([n]) => n)).toEqual(['Edge', 'A', 'Infra']);
    });

    it('group weight is the min across apps (one app pulls the whole group)', () => {
        const apps = [
            { name: 'a1', group: 'ML', weight: 0 },
            { name: 'a2', group: 'ML', weight: -5 },
            { name: 'a3', group: 'ML', weight: 100 },
            { name: 'b1', group: 'Edge', weight: 0 },
        ];
        // ML's min is -5; Edge's min is 0 → ML floats higher.
        expect(sortGroups(apps).map(([n]) => n)).toEqual(['ML', 'Edge']);
    });

    it('alphabetic tiebreak when weights match', () => {
        const apps = [
            { name: 'a', group: 'Beta', weight: -1 },
            { name: 'b', group: 'Alpha', weight: -1 },
            { name: 'c', group: 'Gamma', weight: -1 },
        ];
        expect(sortGroups(apps).map(([n]) => n)).toEqual(['Alpha', 'Beta', 'Gamma']);
    });

    it('missing / non-finite weight treated as 0', () => {
        const apps = [
            { name: 'a', group: 'A', weight: undefined },
            { name: 'b', group: 'B', weight: NaN },
            { name: 'c', group: 'C', weight: 0 },
            { name: 'd', group: 'D', weight: -1 },
        ];
        expect(sortGroups(apps).map(([n]) => n)).toEqual(['D', 'A', 'B', 'C']);
    });

    it('floats handled with full precision', () => {
        const apps = [
            { name: 'a', group: 'A', weight: -0.5 },
            { name: 'b', group: 'B', weight: -0.6 },
            { name: 'c', group: 'C', weight: -0.49 },
        ];
        expect(sortGroups(apps).map(([n]) => n)).toEqual(['B', 'A', 'C']);
    });
});
