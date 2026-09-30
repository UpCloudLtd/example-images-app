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
  <h1><img class="logo" src="/logo.svg" alt="" width="48" height="48" />Images</h1>
  <p class="intro">
    This is an example application used to demonstrate how to deploy an application using various different managed cloud services.
    The images are stored in an object storage and metadata is tracked in a database.
  </p>

  <form on:submit={generate}>
    <label for="description">Description</label>
    <input id="description" type="text" bind:value={description} />
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
  :global(:root) {
    color-scheme: dark;
    --theme: #7b00ff;
    --theme-hover: #8f24ff;
    /* Lighter tint for text: the theme color itself is too dark to read on the background. */
    --theme-text: #b98aff;
    --background: #0f0d14;
    --surface: #1a1722;
    --border: #2e2939;
    --text: #ece9f2;
    --muted: #a39db0;
    --danger-text: #fca5b5;
  }
  :global(body) {
    margin: 0;
    background: var(--background);
    color: var(--text);
  }
  main {
    font-family: sans-serif;
    max-width: 60rem;
    margin: 0 auto;
    padding: 1rem;
  }
  h1 {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
    font-weight: 300;
    color: var(--theme-text);
  }
  h1 .logo {
    width: 3rem;
    height: 3rem;
    aspect-ratio: auto;
  }
  .intro {
    max-width: 36rem;
    margin: 0 auto 2rem;
    color: var(--muted);
  }
  form {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
  }
  label {
    flex-basis: 100%;
    color: var(--muted);
  }
  input {
    flex: 1;
    min-width: 12rem;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: 0.25rem;
    background: var(--surface);
    color: var(--text);
  }
  input:focus-visible,
  button:focus-visible {
    outline: 2px solid var(--theme-text);
    outline-offset: 2px;
  }
  button {
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--theme);
    border-radius: 0.25rem;
    background: var(--theme);
    color: #fff;
    cursor: pointer;
  }
  button:hover:not(:disabled) {
    background: var(--theme-hover);
  }
  button:disabled {
    opacity: 0.6;
    cursor: default;
  }
  li button {
    background: transparent;
    color: var(--theme-text);
  }
  li button:hover:not(:disabled) {
    background: var(--theme);
    color: #fff;
  }
  ul {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr));
    gap: 1rem;
    list-style: none;
    padding: 0;
  }
  li {
    padding: 0.75rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    background: var(--surface);
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
    background: #241c33;
    color: var(--muted);
  }
  .pending strong {
    color: var(--theme-text);
  }
  .failed {
    background: #3a1620;
    color: var(--danger-text);
  }
  [role='alert'] {
    color: var(--danger-text);
  }
  .status span {
    overflow-wrap: anywhere;
  }
  small {
    display: block;
    color: var(--muted);
  }
</style>
