export interface GalleryImage {
  id: number;
  /** Site-relative; served by the backend through the /crm-api proxy. */
  url: string;
  category: string;
  category_display: string;
  caption: string;
  year: number | null;
}

interface GalleryResponse {
  success: boolean;
  count: number;
  images: GalleryImage[];
}

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_API_BASE ?? '';

/** The gallery photos staff manage in the CRM admin, in display order. */
export async function fetchGallery(): Promise<GalleryImage[]> {
  const response = await fetch(`${API_BASE}/crm-api/gallery/`, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Failed to load gallery (status ${response.status})`);
  }
  const result = (await response.json()) as GalleryResponse;
  if (!result.success) {
    throw new Error('Failed to load gallery');
  }
  return result.images;
}
