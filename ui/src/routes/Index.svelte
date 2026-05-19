<script>
    import { onMount } from 'svelte';
    import { listApps } from '../lib/api.js';
    import { config } from '../lib/store.svelte.js';
    import AppCard from '../lib/components/AppCard.svelte';
    import SearchBar from '../lib/components/SearchBar.svelte';

    let apps = $state([]);
    let loading = $state(true);
    let error = $state(null);
    let query = $state('');

    onMount(async () => {
        try {
            apps = await listApps();
        } catch (e) {
            error = e.message || 'Failed to load applications';
        } finally {
            loading = false;
        }
    });

    function matches(app, q) {
        if (!q) return true;
        const needle = q.toLowerCase();
        return (
            (app.title || '').toLowerCase().includes(needle) ||
            (app.description || '').toLowerCase().includes(needle) ||
            (app.group || '').toLowerCase().includes(needle)
        );
    }

    let filtered = $derived(apps.filter((a) => matches(a, query)));

    /**
     * Two-axis ordering driven by Application annotations:
     *
     *   `kex/groupweight` (per app) → group's effective weight is the min
     *     across its apps; lower floats the *group* higher on the page.
     *   `kex/weight` (per app) → app's position *within* its group; lower
     *     sorts earlier. Ties break on title (then name) for stable order.
     *
     * Missing / non-finite annotations default to 0 on both axes.
     */
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

    let groups = $derived.by(() => {
        const m = new Map();
        for (const app of filtered) {
            const g = app.group || 'Other';
            if (!m.has(g)) m.set(g, []);
            m.get(g).push(app);
        }
        // Sort apps within each group by (weight, title, name).
        for (const items of m.values()) {
            items.sort(appSortKey);
        }
        // Sort groups by min-groupweight, with localeCompare tiebreak.
        return [...m.entries()].sort(([aName, aApps], [bName, bApps]) => {
            const dw = groupWeight(aApps) - groupWeight(bApps);
            return dw !== 0 ? dw : aName.localeCompare(bName);
        });
    });
</script>

<section class="hero">
    <div class="hero-text">
        <h1>EdgeLab</h1>
        <p class="tagline">Boliden's Kubernetes cluster for ML research and edge operations.</p>
    </div>
    <SearchBar bind:value={query} />
</section>

{#if loading}
    <p class="state">Loading applications…</p>
{:else if error}
    <p class="state error">Failed to load applications: {error}</p>
{:else if apps.length === 0}
    <section class="empty">
        <h2>No applications registered yet</h2>
        <p>
            Add <code>kex/enabled: "true"</code> and friends to your ArgoCD
            <code>Application</code> CR to see it here.
        </p>
        <pre><code>{`metadata:
  annotations:
    kex/enabled: "true"
    kex/title: "My App"
    kex/description: "What it does"
    kex/group: "My team"`}</code></pre>
    </section>
{:else if filtered.length === 0}
    <p class="state">No matches for "{query}".</p>
{:else}
    {#each groups as [group, items] (group)}
        <section class="group">
            <h2>{group}</h2>
            <div class="grid">
                {#each items as app (app.name)}
                    <AppCard {app} />
                {/each}
            </div>
        </section>
    {/each}
{/if}

<style>
    .hero {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 2rem;
        padding: 3rem 0 2.5rem;
        flex-wrap: wrap;
    }

    .welcome {
        background: var(--ctp-mantle);
        border: 1px solid var(--ctp-surface0);
        border-radius: 12px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 2rem;
        color: var(--ctp-subtext1);
        line-height: 1.55;
    }

    .welcome :global(p) {
        margin: 0 0 0.75rem;
        max-width: 70ch;
    }

    .welcome :global(p:last-child) {
        margin-bottom: 0;
    }

    .welcome :global(a) {
        color: var(--ctp-mauve);
    }

    .welcome :global(code) {
        font-family: var(--font-mono);
        background: var(--ctp-crust);
        padding: 0.05rem 0.3rem;
        border-radius: 4px;
        color: var(--ctp-green);
    }

    .hero-text {
        flex: 1;
        min-width: 280px;
    }

    h1 {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--ctp-mauve), var(--ctp-lavender), var(--ctp-sky));
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 0.5rem;
        line-height: 1.1;
    }

    .tagline {
        color: var(--ctp-subtext1);
        font-size: 1.05rem;
        max-width: 60ch;
    }

    .group {
        margin-bottom: 2rem;
    }

    .group h2 {
        font-size: 1.05rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--ctp-subtext0);
        margin-bottom: 1rem;
    }

    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1rem;
    }

    .state {
        padding: 2rem 0;
        color: var(--ctp-subtext0);
    }

    .state.error {
        color: var(--ctp-red);
    }

    .empty {
        margin-top: 3rem;
        padding: 2rem;
        background: var(--ctp-mantle);
        border: 1px solid var(--ctp-surface0);
        border-radius: 12px;
    }

    .empty h2 {
        font-size: 1.2rem;
        margin-bottom: 0.8rem;
        color: var(--ctp-text);
    }

    .empty p {
        color: var(--ctp-subtext0);
        margin-bottom: 1rem;
    }

    pre {
        background: var(--ctp-crust);
        padding: 1rem;
        border-radius: 8px;
        overflow-x: auto;
    }

    code {
        font-family: var(--font-mono);
        font-size: 0.85rem;
        color: var(--ctp-green);
    }
</style>
