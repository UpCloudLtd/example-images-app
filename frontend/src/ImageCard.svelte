<script>
  let { image, ondelete } = $props();

  function formatDate(value) {
    return new Date(value).toISOString().replace(/\.\d{3}Z$/, "Z");
  }
</script>

<li>
  {#if image.state === "ready"}
    <img src="/api/images/{image.id}/image" alt={image.description} />
  {:else if image.state === "error"}
    <div class="status failed">
      <strong>Error</strong>
      <span>{image.state_details}</span>
    </div>
  {:else}
    <div class="status pending">
      <strong>{image.state === "generating" ? "Generating" : "Pending"}</strong>
      <span>{image.state_details}</span>
    </div>
  {/if}
  <code class="filename">{image.filename}</code>
  <p>{image.description}</p>
  <dl class="timestamps">
    <dt>Requested:</dt>
    <dd>
      <time datetime={formatDate(image.requested_at)}
        >{formatDate(image.requested_at)}</time
      >
    </dd>
    <dt>Generated:</dt>
    <dd>
      {#if image.generated_at}
        <time datetime={formatDate(image.generated_at)}
          >{formatDate(image.generated_at)}</time
        >
      {:else}
        N/A
      {/if}
    </dd>
  </dl>
  <div class="actions">
    {#if image.state === "ready"}
      <a
        class="show"
        href="/api/images/{image.id}/image"
        target="_blank"
        rel="noopener noreferrer">Show</a
      >
    {/if}
    <button
      type="button"
      class="delete"
      onclick={() => ondelete(image.id)}>Delete</button
    >
  </div>
</li>

<style>
  li {
    --card-padding: 0.666rem;
    display: flex;
    flex-direction: column;
    padding: var(--card-padding);
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    background: var(--surface);
    overflow: hidden;
  }
  img,
  .status {
    /* Bleed over the card padding so the image reaches the card edges. */
    width: calc(100% + 2 * var(--card-padding));
    margin: calc(-1 * var(--card-padding)) calc(-1 * var(--card-padding))
      0.25rem;
    aspect-ratio: 1;
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
  .filename {
    color: var(--theme-text);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.666rem;
    overflow-wrap: anywhere;
    margin: 0.333em 0;
    overflow-wrap: anywhere;
  }
  p {
    height: 44px;
    overflow-y: scroll;
    scrollbar-color: var(--muted) transparent;
    scrollbar-width: thin;
  }
  .timestamps {
    display: grid;
    grid-template-columns: auto 1fr;
    align-items: baseline;
    gap: 0.125rem 0.5rem;
    margin: 0;
    font-size: 0.666rem;
    color: var(--muted);
  }
  .timestamps dd {
    margin: 0;
  }
  time {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  .actions {
    display: flex;
    justify-content: center;
    margin-top: auto;
    padding-top: 0.75rem;
  }
  .show,
  .delete {
    padding: 0.25rem 0.5rem 0.2rem;
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
