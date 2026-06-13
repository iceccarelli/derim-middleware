import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import Header from './Header';
import CinematicBackground from './CinematicBackground';
import Analytics from './Analytics';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://derim-middleware.vercel.app'),
  title: {
    default: 'DERIM | Distributed Energy Resource Integration Middleware for Smart Grids',
    template: '%s | DERIM',
  },
  description:
    'Open-source modular middleware that bridges heterogeneous DER hardware (solar PV inverters, BESS, EV chargers) to modern smart grid systems. Pluggable adapters (Modbus, MQTT, SunSpec, OCPP) • IEEE 2030.5 & IEC 61968 CIM normalization • PyTorch Digital Twin • FastAPI REST API • InfluxDB time-series • Full observability. An open foundation (Beta, v0.1.x) for utilities, VPPs, and grid modernization. Explore the live interactive command center.',
  keywords: [
    'DERIM',
    'Distributed Energy Resource Integration Middleware',
    'Smart Grid Middleware',
    'DER Integration',
    'Modbus Adapter',
    'SunSpec Adapter',
    'OCPP Adapter',
    'MQTT for Energy',
    'IEEE 2030.5',
    'IEC 61968 CIM',
    'PyTorch Digital Twin',
    'InfluxDB Telemetry',
    'FastAPI DER API',
    'Grid Modernization',
    'Virtual Power Plant',
    'Battery Energy Storage Systems',
    'EV Charging Integration',
    'Live DER Command Center',
    'Interactive DER Demo',
  ],
  authors: [{ name: 'Vincenzo Grimaldi', url: 'https://github.com/iceccarelli' }],
  creator: 'Vincenzo Grimaldi',
  publisher: 'DERIM Project',
  alternates: { canonical: '/' },
  openGraph: {
    title: 'DERIM | Distributed Energy Resource Integration Middleware',
    description: 'The missing middleware layer for smart grids. Securely bridge solar, storage, and EV assets to SCADA, VPPs, and DERMS with standardized adapters, CIM models, and AI-powered digital twins. Open source on GitHub. Try the live interactive demo.',
    url: 'https://derim-middleware.vercel.app/',
    siteName: 'DERIM',
    locale: 'en_GB',
    type: 'website',
    images: [
      {
        url: 'https://derim-middleware.vercel.app/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'DERIM - Live Interactive DER Command Center for Smart Grids',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'DERIM | Smart Grid DER Middleware • Live Demo',
    description: 'Connect any DER hardware to any grid system. Adapters • CIM • Digital Twin • FastAPI. Open source. Experience the 2050 Command Center.',
    images: ['https://derim-middleware.vercel.app/og-image.jpg'],
  },
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
};

const structuredData = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'DERIM',
  url: 'https://derim-middleware.vercel.app/',
  applicationCategory: 'DeveloperApplication',
  operatingSystem: 'Cross-platform',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'USD',
  },
  description:
    'Lightweight open-source integration middleware that enables seamless, standards-aligned connectivity between distributed energy resources (solar PV, BESS, EV chargers) and smart grid applications through pluggable protocol adapters, CIM normalization, and a PyTorch-powered digital twin engine. Features a production-grade live interactive command center.',
  creator: {
    '@type': 'Person',
    name: 'Vincenzo Grimaldi',
    url: 'https://github.com/iceccarelli',
  },
  sameAs: ['https://github.com/iceccarelli/derim-middleware'],
  featureList: [
    '4+ Production Adapters (Modbus TCP/RTU, MQTT, SunSpec, OCPP 1.6/2.0.1)',
    'IEEE 2030.5 & IEC 61968/61970 CIM-Aligned Data Models',
    'High-Performance InfluxDB Time-Series Storage with SQLite Fallback',
    'PyTorch LSTM Digital Twin for Forecasting, Anomaly Detection & Simulation',
    'Production-Grade FastAPI REST API with OpenAPI 3.1',
    'Full Observability: Structured Logging, Prometheus Metrics, Grafana Dashboards',
    'Docker-First Containerized Deployment with Monitoring & ML Profiles',
    '79+ Unit & Integration Tests Across Core Modules',
    'Live Interactive Command Center Demo (Multi-device, Real-time Charts, CIM Validation, Control Center)',
  ],
  screenshot: 'https://derim-middleware.vercel.app/og-image.jpg',
  softwareVersion: '0.1.1',
  releaseNotes: 'https://github.com/iceccarelli/derim-middleware/releases',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="site-chrome">
          <CinematicBackground />
          <div className="background-orb orb-one" />
          <div className="background-orb orb-two" />
          <div className="background-orb orb-three" />

          <Header />

          {children}

          <footer className="site-footer">
            <div className="section-shell">
              <div className="footer-content">
                {/* Column 1 – Entity */}
                <div>
                  <div className="brand-lockup" style={{ marginBottom: '1rem' }}>
                    <span className="brand-monogram" style={{ width: '42px', height: '42px', fontSize: '1.25rem', background: 'linear-gradient(135deg, #34d399, #10b981)' }}>DM</span>
                    <span className="brand-copy"><strong>DERIM</strong></span>
                  </div>
                  <p style={{ color: 'var(--muted-strong)', lineHeight: '1.6', fontSize: '0.95rem' }}>
                    Distributed Energy Resource Integration Middleware<br />
                    Bridge heterogeneous DER hardware to smart grid systems — deterministically, observably, and securely.<br />
                    <span style={{ color: '#34d399' }}>Open source • Docker-ready • Beta • Live Interactive Demo</span>
                  </p>
                  <p style={{ marginTop: '2rem', fontSize: '0.85rem', color: 'var(--muted)' }}>
                    © 2026 DERIM Project • MIT Licensed • Built by Vincenzo Grimaldi
                  </p>
                </div>

                {/* Column 2 – Platform */}
                <div className="footer-column">
                  <h4>Platform</h4>
                  <div className="footer-links" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <a className="footer-link" href="#architecture">Architecture</a>
                    <a className="footer-link" href="#adapters">Protocol Adapters</a>
                    <a className="footer-link" href="#digital-twin">Digital Twin Engine</a>
                    <a className="footer-link" href="#live-hub">Live Interactive Demo</a>
                    <a className="footer-link" href="https://github.com/iceccarelli/derim-middleware#readme" target="_blank" rel="noopener noreferrer">Documentation</a>
                    <a className="footer-link" href="https://github.com/iceccarelli/derim-middleware/blob/main/ROADMAP.md" target="_blank" rel="noopener noreferrer">Roadmap</a>
                  </div>
                </div>

                {/* Column 3 – Ecosystem */}
                <div className="footer-column">
                  <h4>Ecosystem</h4>
                  <div className="footer-links" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <a className="footer-link" href="https://github.com/iceccarelli/derim-middleware" target="_blank" rel="noopener noreferrer">GitHub Repository</a>
                    <a className="footer-link" href="https://github.com/iceccarelli/derim-middleware/stargazers" target="_blank" rel="noopener noreferrer">Star on GitHub ★</a>
                    <a className="footer-link" href="https://github.com/iceccarelli/derim-middleware/tree/main/notebooks" target="_blank" rel="noopener noreferrer">Jupyter Notebooks</a>
                    <a className="footer-link" href="#live-hub">Try Live Command Center</a>
                    <div className="footer-status">
                      <span className="live-dot" />
                      <span>Active Development • v0.1.1</span>
                    </div>
                  </div>
                </div>

                {/* Column 4 – System Status */}
                <div className="footer-column">
                  <h4>System Status</h4>
                  <div className="footer-status" style={{ marginBottom: '1rem' }}>
                    <span className="live-dot" />
                    <span style={{ color: 'var(--success)', fontWeight: 600 }}>Active Beta • Self-host today</span>
                  </div>
                  <p style={{ color: 'var(--muted)', fontSize: '0.9rem', lineHeight: '1.55' }}>
                    Self-host anywhere • Docker Compose ready<br />
                    Connect your DER assets today.<br />
                    <span style={{ color: '#34d399' }}>Live Interactive Demo available below</span>
                  </p>
                  <a 
                    href="https://github.com/iceccarelli/derim-middleware" 
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: 'var(--accent-strong)', marginTop: '1.5rem', display: 'inline-block' }}
                  >
                    Clone &amp; Deploy on GitHub →
                  </a>
                </div>
              </div>
            </div>
          </footer>
        </div>

        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
        <Analytics />
      </body>
    </html>
  );
}
