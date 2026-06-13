import Script from 'next/script';

/**
 * Privacy-friendly analytics (Plausible). Cookieless, GDPR-friendly — important
 * for an EU-facing infra audience (no consent banner required for Plausible).
 *
 * Enable by setting in Vercel env:  NEXT_PUBLIC_PLAUSIBLE_DOMAIN=derim-middleware.vercel.app
 * Renders nothing until configured, so it is safe to merge immediately.
 */
export default function Analytics() {
  const domain = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN;
  if (!domain) return null;
  return (
    <Script
      defer
      data-domain={domain}
      src="https://plausible.io/js/script.js"
      strategy="afterInteractive"
    />
  );
}
