<script>
    import { onMount } from 'svelte';
    import Router from 'svelte-spa-router';
    import Index from './routes/Index.svelte';
    import AppDetail from './routes/AppDetail.svelte';
    import ThemeToggle from './lib/components/ThemeToggle.svelte';
    import { config, hydrateConfig } from './lib/store.svelte.js';

    const routes = {
        '/': Index,
        '/apps/:name': AppDetail,
    };

    onMount(() => {
        hydrateConfig();
    });
</script>

<header>
    <a href="#/" class="brand">
        <span class="brand-mark">kex</span>
        {#if config.cluster_name}
            <span class="brand-sub">{config.cluster_name}</span>
        {/if}
    </a>
    <div class="header-spacer"></div>
    {#if config.header_links.length > 0}
        <nav class="header-links" aria-label="Cluster links">
            {#each config.header_links as link (link.url)}
                <a href={link.url} target="_blank" rel="noopener">
                    {#if link.icon}
                        <span class="link-icon" aria-hidden="true">📖</span>
                    {/if}
                    {link.label}
                </a>
            {/each}
        </nav>
    {/if}
    <ThemeToggle />
</header>

<main>
    <Router {routes} />
</main>

<style>
    header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem 2rem;
        border-bottom: 1px solid var(--ctp-surface0);
        background: var(--ctp-mantle);
    }

    .brand {
        display: flex;
        align-items: baseline;
        gap: 0.6rem;
        text-decoration: none;
        color: var(--ctp-text);
    }

    .brand-mark {
        font-family: var(--font-mono);
        font-size: 1.4rem;
        font-weight: 600;
        color: var(--ctp-mauve);
    }

    .brand-sub {
        font-size: 0.95rem;
        color: var(--ctp-subtext0);
    }

    .header-spacer {
        flex: 1;
    }

    .header-links {
        display: flex;
        gap: 0.5rem;
    }

    .header-links a {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.35rem 0.7rem;
        font-size: 0.88rem;
        color: var(--ctp-text);
        background: var(--ctp-surface0);
        border: 1px solid var(--ctp-surface1);
        border-radius: 6px;
        text-decoration: none;
        transition: background-color 150ms ease, border-color 150ms ease;
    }

    .header-links a:hover {
        background: var(--ctp-surface1);
        border-color: var(--ctp-mauve);
        text-decoration: none;
    }

    .link-icon {
        font-size: 0.9rem;
    }

    main {
        max-width: 1280px;
        margin: 0 auto;
        padding: 2rem;
    }
</style>
