'use client';

import { useSyncExternalStore } from 'react';
import {
  CINEMATIC_SOURCES, CINEMATIC_PARAMS, HERO_OFFSET,
  activeIndex, getServerTick, getTick, subscribeTick,
} from './cinematic';

export default function HeroBridge() {
  const tick = useSyncExternalStore(subscribeTick, getTick, getServerTick);
  const active = activeIndex(tick, HERO_OFFSET);
  return (
    <div className="hero-portrait-shell hero-bridge">
      {CINEMATIC_SOURCES.map((src, i) => (
        <div
          key={src}
          className={'hero-bridge__media' + (i === active ? ' is-active' : '')}
          style={{ backgroundImage: `url("${src}${CINEMATIC_PARAMS}")` }}
        />
      ))}
      <div className="hero-bridge__scrim" />
      <span className="hero-bridge__live">
        <i className="hero-bridge__live-dot" />
        LIVE
      </span>
      <div className="hero-bridge__content">
        <div className="hero-bridge__nodes" aria-hidden="true">
          <span className="hero-bridge__node" title="Solar PV">☀️</span>
          <span className="hero-bridge__node" title="Battery storage">🔋</span>
          <span className="hero-bridge__node" title="EV charging">🚗</span>
          <span className="hero-bridge__flow"><i /><i /><i /></span>
          <span className="hero-bridge__node hero-bridge__node--grid" title="Smart grid">🏙️</span>
        </div>
        <div className="hero-bridge__title">DERIM</div>
        <div className="hero-bridge__sub">Live DER ↔ Smart Grid Bridge</div>
      </div>
    </div>
  );
}
