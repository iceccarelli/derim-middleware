'use client';

import { useEffect, useSyncExternalStore } from 'react';
import {
  CINEMATIC_SOURCES, CINEMATIC_PARAMS, activeIndex,
  activateCinematic, getServerTick, getTick, subscribeTick,
} from './cinematic';

export default function CinematicBackground() {
  const tick = useSyncExternalStore(subscribeTick, getTick, getServerTick);
  useEffect(() => { activateCinematic(); }, []);
  const active = activeIndex(tick, 0);
  return (
    <div className="cinematic-bg" aria-hidden="true">
      {CINEMATIC_SOURCES.map((src, i) => (
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
