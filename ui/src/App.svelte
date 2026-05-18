<script>
    import Router from 'svelte-spa-router';
    import Index from './routes/Index.svelte';
    import AppDetail from './routes/AppDetail.svelte';
    import ThemeToggle from './lib/components/ThemeToggle.svelte';

    const routes = {
        '/': Index,
        '/apps/:name': AppDetail,
    };
</script>

<header>
    <a href="#/" class="brand">
        <span class="brand-mark">kex</span>
        <span class="brand-sub">EdgeLab</span>
    </a>
    <div class="header-spacer"></div>
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

    main {
        max-width: 1280px;
        margin: 0 auto;
        padding: 2rem;
    }
</style>
