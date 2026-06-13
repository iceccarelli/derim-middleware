import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description: 'How the DERIM project handles the limited personal data it collects.',
};

export default function PrivacyPage() {
  return (
    <main className="section-shell" style={{ maxWidth: 760, margin: '0 auto', padding: '5rem 1.5rem', lineHeight: 1.7 }}>
      <h1>Privacy Policy</h1>
      <p style={{ color: 'var(--muted)' }}>Last updated: 13 June 2026</p>
      <h2>What we collect</h2>
      <p>If you submit the design-partner form, we collect the email address and any context you
        provide. If analytics are enabled, we use Plausible, a cookieless tool that records only
        aggregate, non-identifying page metrics.</p>
      <h2>How we use it</h2>
      <p>Form submissions are used solely to contact you about the DERIM design-partner programme.
        We do not sell or share your data with third parties for advertising.</p>
      <h2>Retention and your rights</h2>
      <p>We retain submission data only as long as needed to coordinate a pilot. You may request
        access to, or deletion of, your data at any time via the email on our GitHub profile.</p>
      <h2>Self-hosting</h2>
      <p>DERIM is open-source middleware you run yourself. When you self-host you are the data
        controller for telemetry your deployment processes; this policy covers only this website.</p>
    </main>
  );
}
