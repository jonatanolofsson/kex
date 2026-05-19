<script>
    import StatusBadge from './StatusBadge.svelte';

    let { app } = $props();

    // The detail-page-route href. The whole card is clickable via the
    // "stretched link" pattern: the inner <a> has a ::after pseudo
    // that covers the entire card. Quick-link <a>s opt out of the
    // stretch with z-index: 1 so their own clicks aren't intercepted.
    let detailHref = $derived(`#/apps/${encodeURIComponent(app.name)}`);

    // app.links is the array of {label, url} the backend ships on the
    // detail-page response — not on the list response. On the list
    // (card) we only have the structured kex/links.app + kex/links.docs
    // values if the backend chooses to surface them. For now we read
    // them from app.quick_links — populated by the list endpoint when
    // the annotations are present.
    let quickLinks = $derived(
        Array.isArray(app.quick_links)
            ? app.quick_links.filter((q) => q && q.url)
            : [],
    );
</script>

<article
    class="card"
    aria-label={app.title}
    title={app.description || app.title}
>
    {#if app.icon}
        <span class="icon" aria-hidden="true">{app.icon}</span>
    {/if}
    <div class="body">
        <h3>
            <a class="stretch" href={detailHref}>{app.title}</a>
        </h3>
        <p class="desc">{app.description || ''}</p>
        <div class="badges">
            <StatusBadge value={app.sync_status} kind="sync" />
            <StatusBadge value={app.health_status} kind="health" />
        </div>
    </div>
    {#if quickLinks.length > 0}
        <div class="quick-links">
            {#each quickLinks as link (link.label)}
                <a
                    class="quick-link"
                    href={link.url}
                    target="_blank"
                    rel="noopener"
                    aria-label="{app.title}: {link.label}"
                    title={link.label}
                >
                    <span aria-hidden="true">{link.icon || '↗'}</span>
                </a>
            {/each}
        </div>
    {/if}
</article>

<style>
    .card {
        position: relative;
        display: flex;
        gap: 1rem;
        padding: 1rem;
        background: var(--ctp-mantle);
        border: 1px solid var(--ctp-surface0);
        border-radius: 12px;
        color: var(--ctp-text);
        transition:
            transform 150ms ease,
            border-color 150ms ease,
            background 150ms ease;
    }

    .card:hover {
        transform: translateY(-2px);
        border-color: var(--ctp-mauve);
        background: var(--ctp-surface0);
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
    }

    /* Stretched link: covers the card so a click anywhere on the
       card body (except the quick-link anchors) goes to the detail page. */
    .stretch {
        color: var(--ctp-text);
        text-decoration: none;
    }

    .stretch::after {
        content: '';
        position: absolute;
        inset: 0;
        z-index: 0;
        border-radius: inherit;
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
        position: relative;
        z-index: 0;
    }

    .quick-links {
        position: absolute;
        right: 0.6rem;
        bottom: 0.6rem;
        display: flex;
        gap: 0.35rem;
        z-index: 1;
    }

    .quick-link {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.85rem;
        height: 1.85rem;
        border-radius: 6px;
        background: var(--ctp-surface0);
        border: 1px solid var(--ctp-surface1);
        color: var(--ctp-text);
        text-decoration: none;
        transition: background-color 150ms ease, border-color 150ms ease;
    }

    .quick-link:hover {
        background: var(--ctp-surface1);
        border-color: var(--ctp-mauve);
        color: var(--ctp-mauve);
    }
</style>
