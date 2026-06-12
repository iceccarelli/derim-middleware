'use client';

import { useEffect, useSyncExternalStore } from 'react';
import { BACKGROUND_SOURCES, CINEMATIC_PARAMS, backgroundRotator, pick } from './cinematic';

export default function CinematicBackground() {
  const r = backgroundRotator;
  const tick = useSyncExternalStore(r.subscribe, r.getTick, r.getServerTick);
  useEffect(() => { r.activate(); }, [r]);
  const active = pick(BACKGROUND_SOURCES, r.getOrder(), tick);

  return (
    <div className="cinematic-bg" aria-hidden="true">
      {BACKGROUND_SOURCES.map((src, i) => (
        <div
          key={src}
          className={'cinematic-bg__layer is-animated' + (i === active ? ' is-active' : '')}
          style={{ backgroundImage: `url("${src}${CINEMATIC_PARAMS}")` }}
        />
      ))}
      <div className="cinematic-bg__scrim" />
    </div>
  );
}
