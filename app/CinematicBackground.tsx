'use client';

import { useEffect, useState } from 'react';

/**
 * Cinematic, auto-rotating background for DERIM.
 *
 * Energy-infrastructure photography (solar, wind, grid, EV) from Unsplash,
 * served via the Unsplash CDN at a web-optimized size. Images crossfade every
 * few seconds with a slow Ken Burns drift, the order is randomized on every
 * visit, and a dark scrim keeps all foreground content readable. Motion is
 * fully disabled for users who prefer reduced motion.
 *
 * Photos (Unsplash License — free for commercial use, no attribution required):
 *   Solar farm           — Priamo Mendez
 *   Wind turbines (dusk)  — Bernd Dittrich
 *   HV transmission lines — P Anosh
 *   EV charging station   — Mohamed B.
 */

const SOURCES = [
  'https://images.unsplash.com/photo-1677273459827-e212995b079d',
  'https://images.unsplash.com/photo-1713077434883-f935e1fcdb87',
  'https://images.unsplash.com/photo-1696971275047-5d62468bcfb4',
  'https://images.unsplash.com/photo-1755555707544-5f2cea7413c1',
];

// Unsplash CDN params: auto WebP, cover-cropped, 1920px wide, quality 70.
const PARAMS = '?auto=format&fit=crop&w=1920&q=70';
const ROTATE_MS = 7000;

function shuffle(arr: string[]): string[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export default function CinematicBackground() {
  // Deterministic initial order (SSR-safe); shuffled on the client after mount.
  const [order, setOrder] = useState<string[]>(SOURCES);
  const [active, setActive] = useState(0);
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    const shuffled = shuffle(SOURCES);
    setOrder(shuffled);

    // Preload so crossfades never flash a blank frame.
    shuffled.forEach((src) => {
      const img = new window.Image();
      img.src = src + PARAMS;
    });

    const prefersReduced =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) {
      setActive(0);
      return;
    }

    setAnimated(true);
    const timer = setInterval(() => {
      setActive((i) => (i + 1) % shuffled.length);
    }, ROTATE_MS);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="cinematic-bg" aria-hidden="true">
      {order.map((src, i) => (
        <div
          key={src}
          className={
            'cinematic-bg__layer' +
            (animated ? ' is-animated' : '') +
            (i === active ? ' is-active' : '')
          }
          style={{ backgroundImage: `url("${src}${PARAMS}")` }}
        />
      ))}
      <div className="cinematic-bg__scrim" />
    </div>
  );
}
