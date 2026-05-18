<script>
    let { value = $bindable('') } = $props();
</script>

<input
    type="search"
    placeholder="Search apps…"
    bind:value
    aria-label="Search applications"
    class="search"
/>

<style>
    .search {
        font-family: inherit;
        font-size: 0.92rem;
        padding: 0.5rem 0.8rem;
        background: var(--ctp-mantle);
        color: var(--ctp-text);
        border: 1px solid var(--ctp-surface0);
        border-radius: 8px;
        min-width: 240px;
    }

    .search:focus {
        outline: 2px solid var(--ctp-mauve);
        outline-offset: 1px;
    }
</style>
