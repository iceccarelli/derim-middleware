'use client';

/**
 * Cinematic image system for DERIM — two fully separate pools.
 * BACKGROUND_SOURCES (8) drives the full-page background.
 * HERO_SOURCES (8) drives the hero portrait.
 * The pools are disjoint, so background and hero can NEVER show the same photo.
 * Each rotator shuffles its pool once per visit and advances on its own clock.
 * All photos are Unsplash License (free for commercial use).
 */

export const CINEMATIC_PARAMS = '?auto=format&fit=crop&w=1920&q=70';

export const BACKGROUND_SOURCES = [
  'https://images.unsplash.com/photo-1696971275047-5d62468bcfb4',
  'https://images.unsplash.com/photo-1713077434883-f935e1fcdb87',
  'https://images.unsplash.com/photo-1677273459827-e212995b079d',
  'https://images.unsplash.com/photo-1543489816-c87b0f5f7dd4',
  'https://images.unsplash.com/photo-1674606071893-2a9023075f70',
  'https://images.unsplash.com/photo-1413882353314-73389f63b6fd',
  'https://images.unsplash.com/photo-1755555707544-5f2cea7413c1',
  'https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9',
];

export const HERO_SOURCES = [
  'https://images.unsplash.com/photo-1610028290816-5d937a395a49',
  'https://images.unsplash.com/photo-1466611653911-95081537e5b7',
  'https://images.unsplash.com/photo-1521618755572-156ae0cdd74d',
  'https://images.unsplash.com/photo-1473341304170-971dccb5ac1e',
  'https://images.unsplash.com/photo-1629726797843-618688139f5a',
  'https://images.unsplash.com/photo-1694931537779-277fa32ed4a2',
  'https://images.unsplash.com/photo-1536408745983-0f03be6e8a00',
  'https://images.unsplash.com/photo-1509391366360-2e959784a276',
];

export type Rotator = {
  getOrder: () => number[];
  getTick: () => number;
  getServerTick: () => number;
  subscribe: (cb: () => void) => () => void;
  activate: () => void;
};

function createRotator(sources: string[], rotateMs: number): Rotator {
  let order = sources.map((_, i) => i);
  let tick = 0;
  let started = false;
  const listeners = new Set<() => void>();
  const emit = () => listeners.forEach((l) => l());
  const shuffle = (a: number[]) => {
    const r = [...a];
    for (let i = r.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [r[i], r[j]] = [r[j], r[i]];
    }
    return r;
  };
  return {
    getOrder: () => order,
    getTick: () => tick,
    getServerTick: () => 0,
    subscribe: (cb) => {
      listeners.add(cb);
      return () => { listeners.delete(cb); };
    },
    activate: () => {
      if (started || typeof window === 'undefined') return;
      started = true;
      order = shuffle(order);
      tick = Math.floor(Math.random() * sources.length);
      sources.forEach((s) => { const img = new window.Image(); img.src = s + CINEMATIC_PARAMS; });
      emit();
      const reduce =
        typeof window.matchMedia === 'function' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (reduce) return;
      setInterval(() => { tick += 1; emit(); }, rotateMs);
    },
  };
}

export const backgroundRotator = createRotator(BACKGROUND_SOURCES, 7000);
export const heroRotator = createRotator(HERO_SOURCES, 9000);

export function pick(sources: string[], order: number[], tick: number): number {
  const n = sources.length;
  return order[((tick % n) + n) % n];
}
