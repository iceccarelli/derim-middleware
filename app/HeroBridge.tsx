/**
 * Hero bridge visual — the "DER ↔ Smart Grid" portrait in the hero panel.
 *
 * A cinematic grid-at-dusk photograph (Unsplash License) with a slow Ken Burns
 * drift, a dark scrim for legibility, bobbing DER asset glyphs, glowing energy
 * particles that flow toward the grid, a pulsing LIVE badge, and the DERIM
 * wordmark. All motion is pure CSS and disabled under prefers-reduced-motion.
 */
export default function HeroBridge() {
  return (
    <div className="hero-portrait-shell hero-bridge">
      <div className="hero-bridge__media" />
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
          <span className="hero-bridge__flow">
            <i />
            <i />
            <i />
          </span>
          <span className="hero-bridge__node hero-bridge__node--grid" title="Smart grid">
            🏙️
          </span>
        </div>
        <div className="hero-bridge__title">DERIM</div>
        <div className="hero-bridge__sub">Live DER ↔ Smart Grid Bridge</div>
      </div>
    </div>
  );
}
