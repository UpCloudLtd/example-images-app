<script>
  let photos = [];
  let files;
  let description = '';
  let tags = '';

  async function load() {
    photos = await (await fetch('/api/photos')).json();
  }

  async function upload(event) {
    event.preventDefault();
    const body = new FormData();
    body.append('file', files[0]);
    body.append('description', description);
    body.append('tags', tags);

    const response = await fetch('/api/photos', { method: 'POST', body });
    if (!response.ok) {
      alert('Upload failed');
      return;
    }

    description = '';
    tags = '';
    event.target.reset();
    await load();
  }

  load();
</script>

<main>
  <h1>Photos</h1>

  <form on:submit={upload}>
    <input type="file" accept="image/*" bind:files required />
    <input type="text" placeholder="Description" bind:value={description} />
    <input type="text" placeholder="Tags (comma separated)" bind:value={tags} />
    <button type="submit">Upload</button>
  </form>

  <ul>
    {#each photos as photo (photo.id)}
      <li>
        <img src="/api/photos/{photo.id}/image" alt={photo.description} />
        <strong>{photo.filename}</strong>
        <p>{photo.description}</p>
        <small>{photo.tags.join(', ')}</small>
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
  img {
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
    border-radius: 0.25rem;
  }
</style>
