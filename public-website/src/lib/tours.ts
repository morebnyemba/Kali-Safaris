export interface Tour {
  id: number;
  name: string;
  description: string;
  category: string;
  category_display: string;
  location: string;
  base_price: string;
  price_per_adult: string;
  price_per_child: string | null;
  duration_value: number;
  duration_unit: string;
  duration_days: number;
  duration_display: string;
  image_url: string | null;
}

interface ToursResponse {
  success: boolean;
  count: number;
  tours: Tour[];
}

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_API_BASE ?? '';

/**
 * Fetches the same live tour catalogue (Tour + seasonal pricing) that the
 * WhatsApp "View Available Tours" flow reads, so the website never shows a
 * trip that doesn't exist in the backend.
 */
export async function fetchTours(): Promise<Tour[]> {
  const response = await fetch(`${API_BASE}/crm-api/tours/`, {
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`Failed to load tours (status ${response.status})`);
  }

  const result = (await response.json()) as ToursResponse;
  if (!result.success) {
    throw new Error('Failed to load tours');
  }

  return result.tours;
}

export function tourPriceUsd(tour: Tour): number {
  const price = Number(tour.price_per_adult ?? tour.base_price);
  return Number.isFinite(price) ? price : 0;
}
