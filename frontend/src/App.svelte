<script>
  import { onMount } from "svelte";
  import ImageCard from "./ImageCard.svelte";

  const example = "Elephant in the room";

  let images = [];
  let loaded = false;
  let generatorModel = "";
  let description = "";
  let generating = false;
  let error = "";

  async function load() {
    images = await (await fetch("/api/images")).json();
    loaded = true;
  }

  async function loadGenerator() {
    generatorModel = (await (await fetch("/api/generator")).json()).model;
  }

  function generate(event) {
    event.preventDefault();
    return submit(description, true);
  }

  function generateExample(event) {
    event.preventDefault();
    return submit(example, false);
  }

  async function submit(text, clearInput) {
    if (generating) return;

    generating = true;
    error = "";
    try {
      const response = await fetch("/api/images", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: text }),
      });
      const result = await response.json();
      if (!response.ok) {
        error = result.error || "unknown error happened";
        return;
      }

      if (clearInput) description = "";
      await load();
    } catch {
      error = "could not connect to the image generation service";
    } finally {
      generating = false;
    }
  }

  async function remove(id) {
    const response = await fetch(`/api/images/${id}`, { method: "DELETE" });
    if (!response.ok) {
      alert("Delete failed");
      return;
    }
    await load();
  }

  onMount(() => {
    load();
    loadGenerator();
    const poll = setInterval(() => {
      load();
      loadGenerator();
    }, 15000);
    return () => clearInterval(poll);
  });
</script>

<main>
  <h1>
    <img class="logo" src="/logo.svg" alt="" width="48" height="48" />Images
  </h1>
  <p class="intro">
    This is an example application used to demonstrate how to deploy an
    application using various different managed cloud services. Use the form
    below to generate images. The images are stored in an object storage and
    metadata is tracked in a database.
  </p>

  <form on:submit={generate}>
    <label for="description">Description</label>
    <input id="description" type="text" bind:value={description} />
    <button type="submit" disabled={generating}>Generate</button>
  </form>
  {#if error}<p class="helptext" role="alert">
      Generating image failed because <code class="error">{error}</code>
    </p>
  {:else if generatorModel}
    <p class="helptext">Generating images with <code>{generatorModel}</code></p>
  {/if}

  {#if loaded && images.length === 0}
    <div class="empty">
      <p>No images yet.</p>
      <p class="example">
        Try for example:
        <a href="#generate-example" on:click={generateExample}>{example}</a>
      </p>
    </div>
  {:else}
    <ul>
      {#each images as image (image.id)}
        <ImageCard {image} ondelete={remove} />
      {/each}
    </ul>
  {/if}
</main>

<footer>
  <a
    href="https://github.com/UpCloudLtd/example-images-app"
    target="_blank"
    rel="noopener noreferrer">UpCloudLtd / example-images-app</a
  >
</footer>

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
    --danger: #ee6371;
    --danger-text: #fca5b5;
  }
  :global(body) {
    margin: 0;
    background: var(--background);
    color: var(--text);
  }
  :global(#app) {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }
  main {
    flex: 1;
    box-sizing: border-box;
    width: 100%;
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
    gap: 0.25rem 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
  }
  label {
    flex-basis: 100%;
    color: var(--muted);
    font-size: 0.75rem;
    font-weight: 400;
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
    outline: 2px solid #fff;
    outline-offset: 2px;
  }
  button {
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--theme);
    border-radius: 0.25rem;
    background: var(--theme);
    color: #fff;
    font-weight: 600;
    cursor: pointer;
  }
  button:hover:not(:disabled) {
    background: var(--theme-hover);
  }
  button:disabled {
    opacity: 0.6;
    cursor: default;
  }
  ul {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr));
    gap: 1rem;
    margin: 3.5rem 0 0;
    list-style: none;
    padding: 0;
  }
  .empty {
    max-width: 36rem;
    margin: 3.5rem auto 0;
    padding: 2rem 1rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    box-sizing: border-box;
    background: var(--surface);
    color: var(--muted);
    text-align: center;
  }
  .empty p {
    margin: 0;
    font-size: 1.125rem;
  }
  .empty .example {
    margin-top: 1.25rem;
    font-size: 0.875rem;
  }
  .empty a {
    color: var(--theme-text);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    text-decoration: none;
  }
  .empty a:hover {
    text-decoration: underline;
  }
  .empty a:focus-visible {
    border-radius: 0.25rem;
    outline: 2px solid #fff;
    outline-offset: 2px;
  }
  .helptext {
    margin: 0;
    color: var(--muted);
    font-size: 0.75rem;
    text-align: center;
  }
  .helptext code {
    color: var(--theme-text);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  .helptext code.error {
    color: var(--danger-text);
  }
  footer {
    margin: 4rem 1rem 0.666rem;
    font-family: sans-serif;
    font-size: 0.75rem;
    text-align: center;
  }
  footer a {
    border-radius: 0.25rem;
    color: var(--theme-text);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.666rem;
    text-decoration: none;
  }
  footer a:hover {
    text-decoration: underline;
  }
  footer a:focus-visible {
    outline: 2px solid #fff;
    outline-offset: 2px;
  }
</style>
