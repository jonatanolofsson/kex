<script>
    // Phase 0 stub. The real index lands in Phase 2 once /api/apps exists.
</script>

<section class="hero">
    <h1>EdgeLab</h1>
    <p class="tagline">Boliden's Kubernetes cluster for ML research and edge operations.</p>
</section>

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

<style>
    .hero {
        padding: 3rem 0 2rem;
    }

    h1 {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--ctp-mauve), var(--ctp-lavender), var(--ctp-sky));
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin-bottom: 0.5rem;
    }

    .tagline {
        color: var(--ctp-subtext1);
        font-size: 1.05rem;
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
