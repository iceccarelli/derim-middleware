import type { MetadataRoute } from 'next';

const BASE = 'https://derim-middleware.vercel.app';

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return [
    { url: `${BASE}/`,               lastModified: now, changeFrequency: 'weekly',  priority: 1.0 },
    { url: `${BASE}/#architecture`,  lastModified: now, changeFrequency: 'monthly', priority: 0.8 },
    { url: `${BASE}/#adapters`,      lastModified: now, changeFrequency: 'monthly', priority: 0.8 },
    { url: `${BASE}/#digital-twin`,  lastModified: now, changeFrequency: 'monthly', priority: 0.7 },
    { url: `${BASE}/#live-hub`,      lastModified: now, changeFrequency: 'weekly',  priority: 0.7 },
  ];
}
