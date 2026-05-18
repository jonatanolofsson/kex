<script>
    import { onMount } from 'svelte';
    import { getApp } from '../lib/api.js';
    import StatusBadge from '../lib/components/StatusBadge.svelte';

    let { params = {} } = $props();

    let app = $state(null);
    let loading = $state(true);
    let error = $state(null);

    onMount(async () => {
        try {
            app = await getApp(params.name);
        } catch (e) {
            error = e.status === 404 ? '404' : e.message || 'Failed to load';
        } finally {
            loading = false;
        }
    });

    function formatAge(timestamp) {
        if (!timestamp) return '—';
        const ms = Date.now() - new Date(timestamp).getTime();
        const s = Math.floor(ms / 1000);
        if (s < 60) return `${s}s`;
        const m = Math.floor(s / 60);
        if (m < 60) return `${m}m`;
        const h = Math.floor(m / 60);
        if (h < 48) return `${h}h`;
        return `${Math.floor(h / 24)}d`;
    }

    function formatDate(timestamp) {
        if (!timestamp) return '—';
        return new Date(timestamp).toLocaleString();
    }
</script>

<a href="#/" class="back">← EdgeLab</a>

{#if loading}
    <p class="state">Loading…</p>
{:else if error === '404'}
    <section class="error">
        <h1>Not found</h1>
        <p>
            No kex-enabled Application named <code>{params.name}</code> exists. Make sure the
            ArgoCD Application carries <code>kex/enabled: "true"</code>.
        </p>
    </section>
{:else if error}
    <p class="state error">{error}</p>
{:else if app}
    <header class="page-header">
        <div class="head-text">
            <h1>{app.title}</h1>
            {#if app.description}
                <p class="desc">{app.description}</p>
            {/if}
        </div>
        <div class="badges">
            <StatusBadge value={app.sync_status} kind="sync" />
            <StatusBadge value={app.health_status} kind="health" />
        </div>
    </header>

    <div class="layout">
        <main class="main-col">
            {#if app.about_html}
                <section class="card">
                    <h2>About</h2>
                    <!-- about_html is server-side rendered from markdown
                         with HTML disabled in the markdown-it config —
                         see src/kex/routes/apps.py — so this is safe. -->
                    <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                    <div class="about prose">{@html app.about_html}</div>
                </section>
            {/if}

            <section class="card">
                <h2>Pods <span class="ns">in {app.namespace || '—'}</span></h2>
                {#if app.pods.length === 0}
                    <p class="muted">No pods found.</p>
                {:else}
                    <table>
                        <thead>
                            <tr>
                                <th>name</th>
                                <th>phase</th>
                                <th>ready</th>
                                <th>restarts</th>
                                <th>age</th>
                            </tr>
                        </thead>
                        <tbody>
                            {#each app.pods as pod (pod.name)}
                                <tr>
                                    <td class="mono">{pod.name}</td>
                                    <td>{pod.phase}</td>
                                    <td>{pod.ready}</td>
                                    <td>{pod.restarts}</td>
                                    <td>{formatAge(pod.creation_timestamp)}</td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                {/if}
            </section>

            {#if app.ingresses && app.ingresses.length > 0}
                <section class="card">
                    <h2>Exposed URLs</h2>
                    <ul class="ingresses">
                        {#each app.ingresses as ing (ing.host + ing.path)}
                            <li>
                                <a href="https://{ing.host}{ing.path}" target="_blank" rel="noopener">
                                    {ing.host}{ing.path}
                                </a>
                            </li>
                        {/each}
                    </ul>
                </section>
            {/if}
        </main>

        <aside class="side-col">
            {#if app.links && app.links.length > 0}
                <section class="card">
                    <h2>Links</h2>
                    <ul class="links">
                        {#each app.links as link (link.label)}
                            <li>
                                <a href={link.url} target="_blank" rel="noopener">
                                    {link.label}
                                </a>
                            </li>
                        {/each}
                    </ul>
                </section>
            {/if}

            <section class="card">
                <h2>Git</h2>
                {#if app.latest_commit}
                    <div class="commit">
                        <div class="commit-author">{app.latest_commit.author}</div>
                        <div class="commit-date">{formatDate(app.latest_commit.date)}</div>
                        {#if app.latest_commit.message}
                            <div class="commit-msg">{app.latest_commit.message}</div>
                        {/if}
                    </div>
                {:else}
                    <p class="muted">Git data unavailable.</p>
                {/if}

                {#if app.recent_deployers && app.recent_deployers.length > 0}
                    <h3>Recent deployers</h3>
                    <ul class="deployers">
                        {#each app.recent_deployers as d (d.email || d.author)}
                            <li>
                                <span class="mono">{d.author}</span>
                                <span class="muted">{formatDate(d.date)}</span>
                            </li>
                        {/each}
                    </ul>
                {/if}
            </section>
        </aside>
    </div>
{/if}

<style>
    .back {
        font-size: 0.9rem;
        color: var(--ctp-subtext0);
    }

    .page-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1.5rem;
        padding: 1.5rem 0;
        flex-wrap: wrap;
        position: sticky;
        top: 0;
        background: var(--ctp-base);
        z-index: 10;
        border-bottom: 1px solid var(--ctp-surface0);
    }

    h1 {
        font-size: 2rem;
        margin-bottom: 0.3rem;
    }

    .desc {
        color: var(--ctp-subtext1);
    }

    .badges {
        display: flex;
        gap: 0.5rem;
    }

    .layout {
        display: grid;
        grid-template-columns: minmax(0, 2fr) minmax(260px, 1fr);
        gap: 1.5rem;
        padding-top: 1.5rem;
    }

    @media (max-width: 900px) {
        .layout {
            grid-template-columns: 1fr;
        }
    }

    .card {
        background: var(--ctp-mantle);
        border: 1px solid var(--ctp-surface0);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
    }

    .card h2 {
        font-size: 0.95rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--ctp-subtext0);
        margin-bottom: 0.8rem;
    }

    .card h3 {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--ctp-subtext0);
        margin: 1rem 0 0.5rem;
    }

    .ns {
        font-family: var(--font-mono);
        color: var(--ctp-overlay1);
        font-size: 0.8rem;
        text-transform: none;
        letter-spacing: 0;
        margin-left: 0.4rem;
    }

    .about :global(p) {
        margin-bottom: 0.6rem;
        max-width: 70ch;
    }

    .about :global(code) {
        font-family: var(--font-mono);
        background: var(--ctp-crust);
        padding: 0.05rem 0.3rem;
        border-radius: 4px;
        color: var(--ctp-green);
    }

    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
    }

    th {
        text-align: left;
        color: var(--ctp-subtext0);
        font-weight: 500;
        padding: 0.4rem 0.6rem 0.4rem 0;
        border-bottom: 1px solid var(--ctp-surface0);
    }

    td {
        padding: 0.4rem 0.6rem 0.4rem 0;
        border-bottom: 1px solid var(--ctp-surface0);
    }

    .mono {
        font-family: var(--font-mono);
    }

    .muted {
        color: var(--ctp-overlay1);
        font-style: italic;
    }

    .ingresses,
    .links,
    .deployers {
        list-style: none;
        padding: 0;
    }

    .ingresses li,
    .links li,
    .deployers li {
        padding: 0.3rem 0;
    }

    .commit-author {
        font-weight: 600;
    }

    .commit-date {
        color: var(--ctp-subtext0);
        font-size: 0.85rem;
    }

    .commit-msg {
        margin-top: 0.4rem;
        color: var(--ctp-subtext1);
    }

    .state {
        padding: 2rem 0;
        color: var(--ctp-subtext0);
    }

    .state.error {
        color: var(--ctp-red);
    }
</style>
