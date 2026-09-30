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

  it('dispatches delete with the image id', async () => {
    const onDelete = vi.fn();
    const { component } = render(ImageCard, { image });
    component.$on('delete', (event) => onDelete(event.detail));

    await fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    expect(onDelete).toHaveBeenCalledWith(image.id);
  });
});
