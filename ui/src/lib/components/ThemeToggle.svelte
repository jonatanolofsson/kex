<script>
    import { onMount } from 'svelte';
    import { getTheme, toggleTheme } from '../theme.js';

    let theme = $state('mocha');

    onMount(() => {
        theme = getTheme();
    });

    function onClick() {
        toggleTheme();
        theme = getTheme();
    }
</script>

<button onclick={onClick} aria-label="Toggle theme" title="Toggle theme">
    {theme === 'mocha' ? '🌙' : '☀'}
</button>

<style>
    button {
        font-size: 1.1rem;
        padding: 0.35rem 0.6rem;
    }
</style>
