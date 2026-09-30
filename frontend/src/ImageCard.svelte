<script>
  import { createEventDispatcher } from 'svelte';

  export let image;

  const dispatch = createEventDispatcher();

  function formatDate(value) {
    return value ? new Date(value).toLocaleString() : 'Not generated';
  }
</script>

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
  <div class="actions">
    {#if image.state === 'ready'}
      <a class="show" href="/api/images/{image.id}/image" target="_blank" rel="noopener noreferrer">Show</a>
    {/if}
    <button type="button" class="delete" on:click={() => dispatch('delete', image.id)}>Delete</button>
  </div>
</li>

<style>
  li {
    display: flex;
    flex-direction: column;
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
  .status span {
    overflow-wrap: anywhere;
  }
  small {
    display: block;
    color: var(--muted);
  }
  .actions {
    display: flex;
    justify-content: center;
    margin-top: auto;
    padding-top: 0.75rem;
  }
  .show,
  .delete {
    padding: .25rem .5rem .20rem;
    border: none;
    border-radius: 0.25rem;
    background: none;
    font: inherit;
    font-size: 0.875rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
  }
  .show:focus-visible,
  .delete:focus-visible {
    outline: 2px solid #fff;
    outline-offset: 0;
  }
  .show {
    color: var(--theme-text);
  }
  .show:hover {
    color: var(--text);
  }
  .delete {
    color: var(--danger);
  }
  .delete:hover {
    color: var(--danger-text);
  }
</style>
