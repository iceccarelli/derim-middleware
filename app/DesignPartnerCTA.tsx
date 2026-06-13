'use client';

import { useState } from 'react';

// Lead capture for the DERIM design-partner programme.
// Works on static Vercel with NO backend via Formspree:
//   1) make a free form at https://formspree.io -> get an id like "xayzqwer"
//   2) set NEXT_PUBLIC_FORMSPREE_ID in your Vercel env
// If unset, it falls back to a mailto: link so it is never a dead end.

const FORMSPREE_ID = process.env.NEXT_PUBLIC_FORMSPREE_ID ?? '';
const CONTACT_EMAIL = 'hello@derim.dev'; // TODO: set your real inbox

type Status = 'idle' | 'submitting' | 'success' | 'error';

export default function DesignPartnerCTA() {
  const [email, setEmail] = useState('');
  const [context, setContext] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [msg, setMsg] = useState('');

  const endpoint = FORMSPREE_ID ? `https://formspree.io/f/${FORMSPREE_ID}` : '';

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    if (!endpoint) {
      window.location.href =
        `mailto:${CONTACT_EMAIL}?subject=DERIM design partner&body=` +
        encodeURIComponent(`Email: ${email}\nContext: ${context}`);
      return;
    }
    setStatus('submitting'); setMsg('');
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ email, context, source: 'derim-design-partner-cta' }),
      });
      if (res.ok) {
        setStatus('success');
        setMsg("You are on the list. We will reach out within two business days.");
        setEmail(''); setContext('');
      } else {
        setStatus('error'); setMsg('Something went wrong. Email us at ' + CONTACT_EMAIL + '.');
      }
    } catch {
      setStatus('error'); setMsg('Network error. Email us at ' + CONTACT_EMAIL + '.');
    }
  }

  const field: React.CSSProperties = {
    width: '100%', padding: '0.8rem 1rem', borderRadius: '10px',
    border: '1px solid rgba(148,163,184,0.25)', background: 'rgba(2,6,23,0.4)',
    color: 'var(--text, #e2e8f0)', fontSize: '0.95rem', outline: 'none',
  };

  return (
    <section id="design-partners" className="section-shell" style={{ padding: '4rem 0' }}>
      <div style={{
        maxWidth: '680px', margin: '0 auto', textAlign: 'center',
        border: '1px solid rgba(52,211,153,0.25)', borderRadius: '20px',
        padding: '2.5rem 2rem',
        background: 'linear-gradient(180deg, rgba(16,185,129,0.06), rgba(2,6,23,0))',
      }}>
        <span className="section-kicker" style={{ color: '#34d399' }}>Design Partner Programme</span>
        <h2 style={{ fontSize: '1.85rem', margin: '0.75rem 0 0.5rem', lineHeight: 1.2 }}>
          Running a DER integration? Let us help you ship it.
        </h2>
        <p style={{ color: 'var(--muted-strong)', lineHeight: 1.6, maxWidth: '540px', margin: '0 auto 1.75rem' }}>
          We are onboarding a small group of utilities, VPP operators, and OEMs as design partners:
          hands-on integration support and direct input on the roadmap, no cost during the pilot.
        </p>
        {status === 'success' ? (
          <div role="status" style={{ padding: '1rem 1.25rem', borderRadius: '12px',
            background: 'rgba(16,185,129,0.12)', color: 'var(--success)', fontWeight: 600 }}>
            &#10003; {msg}
          </div>
        ) : (
          <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', textAlign: 'left' }}>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="Work email *" aria-label="Work email" style={field} />
            <input type="text" value={context} onChange={(e) => setContext(e.target.value)}
              placeholder="What are you integrating? (optional)" aria-label="Context" style={field} />
            <button type="submit" className="primary-button" disabled={status === 'submitting'}
              style={{ justifyContent: 'center', marginTop: '0.25rem', opacity: status === 'submitting' ? 0.7 : 1 }}>
              {status === 'submitting' ? 'Sending...' : 'Request design-partner access &rarr;'}
            </button>
            {status === 'error' && <p style={{ color: '#f87171', fontSize: '0.9rem', margin: 0 }}>{msg}</p>}
            <p style={{ color: 'var(--muted)', fontSize: '0.8rem', margin: '0.25rem 0 0' }}>
              No spam. We use your email only to coordinate the pilot. See our{' '}
              <a href="/privacy" style={{ color: 'var(--accent-strong)' }}>privacy policy</a>.
            </p>
          </form>
        )}
      </div>
    </section>
  );
}
