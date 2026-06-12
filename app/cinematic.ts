'use client';

/**
 * Shared cinematic image system for DERIM.
 *
 * One pool of energy photos drives BOTH the full-page background and the hero.
 * The order is shuffled once per visit and a single clock advances a shared
 * "tick", so every visitor starts on a different image, the images rotate as
 * you stay, and the hero is offset from the background by HERO_OFFSET — which
 * makes it impossible for the two to show the same photo at once.
 */

export const CINEMATIC_SOURCES = [
  'https://images.unsplash.com/photo-1677273459827-e212995b079d',
  'https://images.unsplash.com/photo-1713077434883-f935e1fcdb87',
  'https://images.unsplash.com/photo-1696971275047-5d62468bcfb4',
  'https://images.unsplash.com/photo-1755555707544-5f2cea7413c1',
];

export const CINEMATIC_PARAMS = '?auto=format&fit=crop&w=1920&q=70';
export const HERO_OFFSET = Math.max(1, Math.floor(CINEMATIC_SOURCES.length / 2));
const ROTATE_MS = 7000;

let order: number[] = CINEMATIC_SOURCES.map((_, i) => i);
let tick = 0;
let started = false;
const listeners = new Set<() => void>();

function emit() { listeners.forEach((l) => l()); }
function shuffle(arr: number[]): number[] {
  const r = [...arr];
  for (let i = r.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [r[i], r[j]] = [r[j], r[i]];
  }
  return r;
}

export function getOrder(): number[] { return order; }
export function getTick(): number { return tick; }
export function getServerTick(): number { return 0; }
export function subscribeTick(cb: () => void): () => void {
  listeners.add(cb);
  return () => { listeners.delete(cb); };
}

export function activateCinematic(): void {
  if (started || typeof window === 'undefined') return;
  started = true;
  order = shuffle(order);
  tick = Math.floor(Math.random() * CINEMATIC_SOURCES.length);
  CINEMATIC_SOURCES.forEach((src) => { const img = new window.Image(); img.src = src + CINEMATIC_PARAMS; });
  emit();
  const reduce = typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) return;
  setInterval(() => { tick += 1; emit(); }, ROTATE_MS);
}

export function activeIndex(t: number, offset = 0): number {
  const n = CINEMATIC_SOURCES.length;
  return order[(((t + offset) % n) + n) % n];
}
