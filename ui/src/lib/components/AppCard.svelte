<script>
    import StatusBadge from './StatusBadge.svelte';

    let { app } = $props();
</script>

<a
    class="card"
    href="#/apps/{encodeURIComponent(app.name)}"
    aria-label={app.title}
    title={app.description || app.title}
>
    {#if app.icon}
        <span class="icon" aria-hidden="true">{app.icon}</span>
    {/if}
    <div class="body">
        <h3>{app.title}</h3>
        <p class="desc">{app.description || ''}</p>
        <div class="badges">
            <StatusBadge value={app.sync_status} kind="sync" />
            <StatusBadge value={app.health_status} kind="health" />
        </div>
    </div>
</a>

<style>
    .card {
        display: flex;
        gap: 1rem;
        padding: 1rem;
        background: var(--ctp-mantle);
        border: 1px solid var(--ctp-surface0);
        border-radius: 12px;
        color: var(--ctp-text);
        text-decoration: none;
        transition:
            transform 150ms ease,
            border-color 150ms ease,
            background 150ms ease;
    }

    .card:hover {
        transform: translateY(-2px);
        border-color: var(--ctp-mauve);
        background: var(--ctp-surface0);
        text-decoration: none;
    }

    .icon {
        font-size: 1.5rem;
        line-height: 1;
        flex-shrink: 0;
        margin-top: 0.1rem;
    }

    .body {
        flex: 1;
        min-width: 0;
    }

    h3 {
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
        color: var(--ctp-text);
    }

    .desc {
        font-size: 0.88rem;
        color: var(--ctp-subtext0);
        margin-bottom: 0.7rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .badges {
        display: flex;
        gap: 0.4rem;
        flex-wrap: wrap;
    }
</style>
