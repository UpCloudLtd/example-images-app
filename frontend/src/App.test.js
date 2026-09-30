import { fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App.svelte';

const images = [
  {
    id: '4f8d6a2e-9c1b-4e7a-8d3f-2b5c6e7f8a90',
    filename: 'riva-del-garda-8lfgq.png',
    description: 'Riva del Garda',
    state: 'ready',
    state_details: 'Generated.',
    requested_at: '2026-09-30T10:00:00+00:00',
    generated_at: '2026-09-30T10:01:00+00:00'
  },
  {
    id: '0c2e4a6b-8d1f-4b3c-9e5a-7f6d8c0b2a14',
    filename: 'donkey-5nf8k.png',
    description: 'Donkey',
    state: 'generating',
    state_details: 'Generating with FLUX.2.',
    requested_at: '2026-09-30T09:00:00+00:00',
    generated_at: null
  },
  {
    id: '9a7b5c3d-1e2f-4a6b-8c0d-e4f6a8b0c2d3',
    filename: 'cat-g9zlw.png',
    description: 'Cat',
    state: 'error',
    state_details: 'RuntimeError: out of memory',
    requested_at: '2026-09-30T08:00:00+00:00',
    generated_at: null
  }
];

function response(body, status = 200) {
  return Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(body) });
}

let fetchMock;

function imageRequests() {
  return fetchMock.mock.calls.filter(([url, options]) => url === '/api/images' && !options);
}

beforeEach(() => {
  fetchMock = vi.fn((url) =>
    url === '/api/generator' ? response({ model: 'builtin/text-on-shapes' }) : response(images)
  );
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('App', () => {
  it('renders images by state', async () => {
    render(App);

    const image = await screen.findByAltText('Riva del Garda');
    expect(image.getAttribute('src')).toBe('/api/images/4f8d6a2e-9c1b-4e7a-8d3f-2b5c6e7f8a90/image');
    expect(screen.getByText('Generating')).toBeTruthy();
    expect(screen.getByText('Generating with FLUX.2.')).toBeTruthy();
    expect(screen.getByText('Error')).toBeTruthy();
    expect(screen.getByText('RuntimeError: out of memory')).toBeTruthy();
    expect(screen.getAllByText('N/A')).toHaveLength(2);
  });

  it('links to the source repository in the footer', () => {
    render(App);

    const link = screen.getByRole('link', { name: 'UpCloudLtd / example-images-app' });
    expect(link.getAttribute('href')).toBe('https://github.com/UpCloudLtd/example-images-app');
    expect(link.getAttribute('target')).toBe('_blank');
    expect(link.getAttribute('rel')).toBe('noopener noreferrer');
    expect(link.closest('footer')).toBeTruthy();
  });

  it('shows the active generator model', async () => {
    render(App);

    expect((await screen.findByText('builtin/text-on-shapes')).tagName).toBe('CODE');
  });

  it('shows a link to open only ready images in a new tab', async () => {
    render(App);
    await screen.findByAltText('Riva del Garda');

    const links = screen.getAllByRole('link', { name: 'Show' });
    expect(links).toHaveLength(1);
    expect(links[0].getAttribute('href')).toBe('/api/images/4f8d6a2e-9c1b-4e7a-8d3f-2b5c6e7f8a90/image');
    expect(links[0].getAttribute('target')).toBe('_blank');
  });

  it('posts the description and reloads images', async () => {
    render(App);
    await screen.findByAltText('Riva del Garda');

    const input = screen.getByLabelText('Description');
    await fireEvent.input(input, { target: { value: 'Riva del Garda' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

    await waitFor(() => expect(imageRequests()).toHaveLength(2));
    expect(fetchMock).toHaveBeenCalledWith('/api/images', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description: 'Riva del Garda' })
    });
    expect(input.value).toBe('');
  });

  it('shows the error returned by the backend', async () => {
    render(App);
    await screen.findByAltText('Riva del Garda');
    fetchMock.mockImplementationOnce(() => response({ error: 'description is required' }, 400));

    await fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

    const alert = await screen.findByRole('alert');
    expect(alert.textContent.replace(/\s+/g, ' ').trim()).toBe('Generating image failed because description is required');
    expect(alert.querySelector('code').textContent).toBe('description is required');
  });

  it('deletes an image and reloads images', async () => {
    render(App);
    await screen.findByAltText('Riva del Garda');

    await fireEvent.click(screen.getAllByRole('button', { name: 'Delete' })[0]);

    await waitFor(() => expect(imageRequests()).toHaveLength(2));
    expect(fetchMock).toHaveBeenCalledWith('/api/images/4f8d6a2e-9c1b-4e7a-8d3f-2b5c6e7f8a90', {
      method: 'DELETE'
    });
  });
});
