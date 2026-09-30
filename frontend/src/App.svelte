<script>
  import { onMount } from 'svelte';

  let images = [];
  let description = '';
  let generating = false;
  let error = '';

  function formatDate(value) {
    return value ? new Date(value).toLocaleString() : 'Not generated';
  }

  async function load() {
    images = await (await fetch('/api/images')).json();
  }

  async function generate(event) {
    event.preventDefault();
    if (generating) return;

    generating = true;
    error = '';
    try {
      const response = await fetch('/api/images', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description })
      });
      const result = await response.json();
      if (!response.ok) {
        error = result.error || 'Image generation failed';
        return;
      }

      description = '';
      await load();
    } catch {
      error = 'Could not connect to the image generation service';
    } finally {
      generating = false;
    }
  }

  async function remove(id) {
    const response = await fetch(`/api/images/${id}`, { method: 'DELETE' });
    if (!response.ok) {
      alert('Delete failed');
      return;
    }
    await load();
  }

  onMount(() => {
    load();
    const poll = setInterval(load, 15000);
    return () => clearInterval(poll);
  });
</script>

<main>
  <h1>Images</h1>

  <form on:submit={generate}>
    <input type="text" placeholder="Description" bind:value={description} />
    <button type="submit" disabled={generating}>{generating ? 'Generating...' : 'Generate image'}</button>
  </form>
  {#if error}<p role="alert">{error}</p>{/if}

  <ul>
    {#each images as image (image.id)}
      <li>
        {#if image.state === 'ready'}
          <img src="/api/images/{image.id}/image" alt={image.description} />
        {:else if image.state === 'error'}
          <div class="status failed">
            <strong>Error</strong>
            <span>{image.state_details}</span>
          </div>
        {:else}
          <div class="status pending">
            <strong>{image.state === 'generating' ? 'Generating' : 'Pending'}</strong>
            <span>{image.state_details}</span>
          </div>
        {/if}
        <strong>{image.filename}</strong>
        <p>{image.description}</p>
        <small>Requested: {formatDate(image.requested_at)}</small>
        <small>Generated: {formatDate(image.generated_at)}</small>
        <button type="button" on:click={() => remove(image.id)}>Delete</button>
      </li>
    {/each}
  </ul>
</main>

<style>
  main {
    font-family: sans-serif;
    max-width: 60rem;
    margin: 0 auto;
    padding: 1rem;
  }
  form {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
  }
  ul {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr));
    gap: 1rem;
    list-style: none;
    padding: 0;
  }
  img,
  .status {
    width: 100%;
    aspect-ratio: 1;
    border-radius: 0.25rem;
  }
  img {
    object-fit: cover;
  }
  .status {
    display: grid;
    place-items: center;
    align-content: center;
    gap: 0.5rem;
    box-sizing: border-box;
    padding: 1rem;
    text-align: center;
  }
  .pending {
    background: #e5e7eb;
    color: #374151;
  }
  .failed {
    background: #fee2e2;
    color: #991b1b;
  }
  .status span {
    overflow-wrap: anywhere;
  }
  small {
    display: block;
  }
</style>
