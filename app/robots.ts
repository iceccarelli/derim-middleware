import type { MetadataRoute } from 'next';

const BASE = 'https://derim-middleware.vercel.app';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: '*', allow: '/' }],
    sitemap: `${BASE}/sitemap.xml`,
    host: BASE,
  };
}
