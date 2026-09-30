import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import ImageCard from './ImageCard.svelte';

const image = {
  id: '4f8d6a2e-9c1b-4e7a-8d3f-2b5c6e7f8a90',
  filename: 'riva-del-garda-8lfgq.png',
  description: 'Riva del Garda',
  state: 'pending',
  state_details: 'Queued for generation.',
  requested_at: '2026-09-30T10:00:00+00:00',
  generated_at: null
};

describe('ImageCard', () => {
  it('shows a placeholder and no Show link until the image is ready', () => {
    render(ImageCard, { image });

    expect(screen.getByText('Pending')).toBeTruthy();
    expect(screen.getByText('Queued for generation.')).toBeTruthy();
    expect(screen.queryByRole('link', { name: 'Show' })).toBeNull();
  });

  it('lists timestamps in ISO 8601 UTC format', () => {
    render(ImageCard, {
      image: {
        ...image,
        state: 'ready',
        requested_at: '2026-09-30T13:00:00+03:00',
        generated_at: '2026-09-30T10:01:30.250000+00:00'
      }
    });

    const requested = screen.getByText('2026-09-30T10:00:00Z');
    expect(requested.tagName).toBe('TIME');
    expect(requested.getAttribute('datetime')).toBe('2026-09-30T10:00:00Z');
    expect(screen.getByText('2026-09-30T10:01:30Z')).toBeTruthy();
    expect(screen.getByText('Requested:').tagName).toBe('DT');
  });

  it('dispatches delete with the image id', async () => {
    const onDelete = vi.fn();
    const { component } = render(ImageCard, { image });
    component.$on('delete', (event) => onDelete(event.detail));

    await fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    expect(onDelete).toHaveBeenCalledWith(image.id);
  });
});
