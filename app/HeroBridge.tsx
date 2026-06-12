'use client';

import { useEffect, useSyncExternalStore } from 'react';
import { HERO_SOURCES, CINEMATIC_PARAMS, heroRotator, pick } from './cinematic';

export default function HeroBridge() {
  const r = heroRotator;
  const tick = useSyncExternalStore(r.subscribe, r.getTick, r.getServerTick);
  useEffect(() => { r.activate(); }, [r]);
  const active = pick(HERO_SOURCES, r.getOrder(), tick);

  return (
    <div className="hero-portrait-shell hero-bridge">
      {HERO_SOURCES.map((src, i) => (
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
