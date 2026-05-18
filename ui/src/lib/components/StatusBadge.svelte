<script>
    /* A small pill rendering an ArgoCD sync / health status. The
       three buckets map to Catppuccin accents so the colour reads as
       semantic regardless of theme. */
    let { value = null, kind = 'sync' } = $props();

    const TONE = {
        Synced: 'good',
        Healthy: 'good',
        OutOfSync: 'warn',
        Progressing: 'warn',
        Degraded: 'bad',
        Missing: 'bad',
        Unknown: 'unknown',
    };

    let tone = $derived(TONE[value] || 'unknown');
    let label = $derived(value || `Unknown ${kind}`);
</script>

<span class="badge tone-{tone}" title="{kind}: {label}">
    <span class="dot"></span>
    {label}
</span>

<style>
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.78rem;
        font-family: var(--font-mono);
        padding: 0.18rem 0.5rem;
        border-radius: 999px;
        background: var(--ctp-surface0);
        color: var(--ctp-subtext1);
        border: 1px solid var(--ctp-surface1);
    }

    .dot {
        width: 0.55rem;
        height: 0.55rem;
        border-radius: 50%;
        background: var(--ctp-overlay1);
    }

    .tone-good .dot {
        background: var(--ctp-green);
    }

    .tone-warn .dot {
        background: var(--ctp-yellow);
    }

    .tone-bad .dot {
        background: var(--ctp-red);
    }

    .tone-unknown .dot {
        background: var(--ctp-overlay0);
    }
</style>
