<script>
    import { onMount } from 'svelte';
    import { listApps } from '../lib/api.js';
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
     * Group weight = min(weights of apps in the group). Lower weight floats
     * the group higher on the landing page. Apps that don't declare a
     * `kex/weight` annotation arrive as `weight: 0`. Ties break on group
     * name via `localeCompare` so the order is deterministic.
     */
    function groupWeight(apps) {
        let min = Infinity;
        for (const app of apps) {
            const w = Number.isFinite(app.weight) ? app.weight : 0;
            if (w < min) min = w;
        }
        return min === Infinity ? 0 : min;
    }

    let groups = $derived.by(() => {
        const m = new Map();
        for (const app of filtered) {
            const g = app.group || 'Other';
            if (!m.has(g)) m.set(g, []);
            m.get(g).push(app);
        }
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
