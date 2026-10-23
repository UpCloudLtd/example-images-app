<script>
  let { tag = "div", children } = $props();
</script>

<svelte:element this={tag} class="card">
  {@render children?.()}
</svelte:element>

<style>
  .card {
    --card-padding: 0.666rem;
    display: flex;
    flex-direction: column;
    padding: var(--card-padding);
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    background: var(--surface);
    overflow: hidden;
  }
</style>
