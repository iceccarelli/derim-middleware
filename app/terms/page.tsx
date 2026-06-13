import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Service',
  description: 'Terms governing use of the DERIM website and software.',
};

export default function TermsPage() {
  return (
    <main className="section-shell" style={{ maxWidth: 760, margin: '0 auto', padding: '5rem 1.5rem', lineHeight: 1.7 }}>
      <h1>Terms of Service</h1>
      <p style={{ color: 'var(--muted)' }}>Last updated: 13 June 2026</p>
      <h2>The software</h2>
      <p>DERIM is provided under the MIT License, on an &quot;as is&quot; basis without warranty of
        any kind. See the LICENSE file in the repository for the full terms.</p>
      <h2>This website</h2>
      <p>Content here is informational. Interactive demos run on illustrative data in your browser
        and do not represent a live production system or a performance guarantee.</p>
      <h2>Design-partner programme</h2>
      <p>Participation is by mutual agreement and carries no purchase obligation. Specific pilot
        terms are agreed separately in writing.</p>
    </main>
  );
}
