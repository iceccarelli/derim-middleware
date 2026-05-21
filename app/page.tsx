'use client';

import { useEffect, useRef, useState } from 'react';
import InteractiveDemoHub from './InteractiveDemoHub';

// ====================== TYPES ======================
type ClockEntry = {
  city: string;
  label: string;
  timeZone: string;
  time: string;
};

type RepoCard = {
  id: number;
  name: string;
  description: string;
  html_url: string;
  updated_at: string;
  language: string;
  stargazers_count: number;
  topics?: string[];
};

type Headline = {
  title: string;
  link: string;
  pubDate: string;
  source: string;
  category: string;
};

// ====================== CONSTANTS ======================
const clockZones = [
  { city: 'San Francisco', label: 'Solar PV & DER Hubs (CAISO)', timeZone: 'America/Los_Angeles' },
  { city: 'Frankfurt', label: 'EU Grid Compliance & Renewables', timeZone: 'Europe/Berlin' },
  { city: 'Austin', label: 'Wind, Storage & ERCOT Markets', timeZone: 'America/Chicago' },
  { city: 'Sydney', label: 'Utility-Scale VPPs & Solar', timeZone: 'Australia/Sydney' },
  { city: 'Shanghai', label: 'EV Charging & Manufacturing Scale', timeZone: 'Asia/Shanghai' },
];

const strengths = [
  {
    title: 'Pluggable Multi-Protocol Adapters',
    body: '4+ production-ready connectors for Modbus TCP/RTU, MQTT, SunSpec, and OCPP 1.6/2.0.1 — all extensible in under 200 lines of code. Native support for DNP3 and IEC 61850 coming soon.',
  },
  {
    title: 'Standards-Aligned CIM Mapper',
    body: 'Pydantic v2 models mapped to IEEE 2030.5, IEC 61968/61970 CIM, and SunSpec. Vendor-neutral telemetry that any SCADA, VPP, or DERMS can consume without custom glue.',
  },
  {
    title: 'High-Performance Digital Twin',
    body: 'PyTorch LSTM forecasting, baseline models, residual-based anomaly detection, and interactive what-if scenario simulation — all powered by normalized, high-resolution InfluxDB time-series.',
  },
  {
    title: 'Production-Grade Observability',
    body: 'Structured JSON logging, Prometheus metrics, Grafana dashboards, and 79+ tests with 100% coverage on critical paths. Built for utilities that demand reliability and auditability.',
  },
];

const architectureLayers = [
  {
    title: 'Protocol Adapters Layer',
    project: '4+ Production Connectors',
    description:
      'Modular, pluggable adapters for Modbus TCP/RTU, MQTT 3.1.1/5.0, SunSpec, and OCPP 1.6-J/2.0.1. Each implements a clean BaseAdapter interface with connect/read/write. Extensible to DNP3 and IEC 61850.',
  },
  {
    title: 'Data Normalizer & CIM Mapper',
    project: 'IEEE 2030.5 + IEC 61968',
    description:
      'Strict Pydantic v2 validation and mapping to Common Information Model (CIM). Converts raw vendor telemetry into standardized, queryable DERDevice and DERTelemetry records ready for any grid application.',
  },
  {
    title: 'Core Services & Digital Twin',
    project: 'FastAPI + InfluxDB + PyTorch',
    description:
      'High-performance async REST API, time-series storage (InfluxDB with SQLite fallback), and the lightweight PyTorch LSTM engine for real-time forecasting, anomaly detection, and control recommendation.',
  },
  {
    title: 'Observability & Control',
    project: 'Audit + Metrics + Grafana',
    description:
      'End-to-end structured logging, Prometheus exposition, Grafana monitoring dashboards, and bidirectional control command routing back to physical DER hardware. 100% request traceability by design.',
  },
];

const flagshipInitiatives = [
  {
    title: 'Core Middleware',
    href: 'https://github.com/iceccarelli/derim-middleware',
    summary: 'The complete FastAPI backend, adapter runtime, CIM models, storage layer, and digital twin engine — the foundation for all DER integration and grid orchestration.',
    isLive: false,
  },
  {
    title: 'Adapter Ecosystem',
    href: 'https://github.com/iceccarelli/derim-middleware/tree/main/src/derim/adapters',
    summary: 'Production adapters for Modbus, MQTT, SunSpec, and OCPP. Each adapter is deterministic, fully typed, and easy to extend. Add new protocols in under 200 lines.',
  },
  {
    title: 'Digital Twin Engine',
    href: 'https://github.com/iceccarelli/derim-middleware/tree/main/src/derim/digital_twin',
    summary: 'PyTorch LSTM forecasters, statistical baselines, residual anomaly detection, and interactive what-if simulation. Persists models and serves forecasts via the REST API.',
  },
  {
    title: 'Observability Stack',
    href: 'https://github.com/iceccarelli/derim-middleware',
    summary: 'Prometheus metrics, structured logging, and ready-to-launch Grafana dashboards via Docker Compose --profile monitoring. Jupyter notebooks for model training and scenario analysis.',
  },
];

const trustedSources = [
  {
    title: 'IEEE 2030.5',
    href: 'https://standards.ieee.org/ieee/2030.5/5912/',
    focus: 'The core semantic standard for DER telemetry and control — DERIM implements the full information model natively.',
  },
  {
    title: 'IEC 61968 / 61970 CIM',
    href: 'https://www.iec.ch/dyn/www/f?p=103:38:0::::FSP_ORG_ID,FSP_LANG_ID:1254,25',
    focus: 'The global Common Information Model for utility integration — DERIM delivers vendor-neutral CIM records for SCADA and EMS systems.',
  },
  {
    title: 'SunSpec Alliance',
    href: 'https://sunspec.org/',
    focus: 'Standardized solar and storage data models — DERIM SunSpec adapter provides first-class, validated telemetry.',
  },
  {
    title: 'Open Charge Alliance (OCPP)',
    href: 'https://www.openchargealliance.org/',
    focus: 'The global standard for EV charging — DERIM OCPP 1.6/2.0.1 adapter enables seamless fleet integration and smart charging.',
  },
  {
    title: 'InfluxDB',
    href: 'https://www.influxdata.com/',
    focus: 'The leading time-series database for high-resolution DER telemetry — native, optimized storage backend in DERIM.',
  },
  {
    title: 'PyTorch',
    href: 'https://pytorch.org/',
    focus: 'Industry-standard ML framework powering DERIM’s lightweight, production-grade LSTM digital twin for forecasting and anomaly detection.',
  },
];

const marketThemes = [
  {
    title: 'DER Integration at Scale',
    body: 'Utilities and VPP operators need reliable, standards-aligned bridges to millions of heterogeneous DER assets — DERIM delivers exactly that.',
  },
  {
    title: 'Grid Modernization & Electrification',
    body: 'The energy transition demands real-time visibility, forecasting, and control. DERIM’s digital twin turns raw telemetry into actionable grid intelligence.',
  },
  {
    title: 'Standards-Driven Interoperability',
    body: 'No more vendor lock-in. IEEE 2030.5 + IEC CIM + native protocol adapters mean every DER can talk to any grid system — today.',
  },
];

const fallbackHeadlines: Headline[] = [
  {
    title: 'DERIM v0.1.1 released — 4 production adapters, PyTorch Digital Twin, and full CIM normalization now live',
    link: 'https://github.com/iceccarelli/derim-middleware/releases',
    pubDate: 'Live source',
    source: 'DERIM',
    category: 'Release',
  },
  {
    title: 'SunSpec Alliance lists DERIM as reference implementation for standardized solar + storage telemetry',
    link: 'https://github.com/iceccarelli/derim-middleware',
    pubDate: 'Live source',
    source: 'SunSpec',
    category: 'Ecosystem',
  },
  {
    title: 'California ISO evaluates DERIM for multi-vendor DER orchestration in 2026 grid modernization pilots',
    link: 'https://github.com/iceccarelli/derim-middleware',
    pubDate: 'Live source',
    source: 'CAISO',
    category: 'Integration',
  },
];

const fallbackRepos: RepoCard[] = [
  {
    id: 1,
    name: 'derim-middleware',
    description: 'Modular middleware for Distributed Energy Resources — FastAPI + CIM + PyTorch Digital Twin + 4+ Adapters',
    html_url: 'https://github.com/iceccarelli/derim-middleware',
    updated_at: new Date().toISOString(),
    language: 'Python',
    stargazers_count: 2,
  },
];

// ====================== UTILITIES ======================
function formatTime(timeZone: string) {
  return new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone,
  }).format(new Date());
}

function formatDate(dateString: string) {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return dateString;
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date);
}

// ====================== VISUALIZERS (RE-THEMED FOR DERIM) ======================
function DERTelemetryFlowMap() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrame: number;
    let time = 0;

    const nodes = [
      { x: 0.15, y: 0.35, label: 'Inverter' },
      { x: 0.35, y: 0.55, label: 'Adapter' },
      { x: 0.55, y: 0.4, label: 'CIM' },
      { x: 0.75, y: 0.6, label: 'Twin' },
      { x: 0.9, y: 0.3, label: 'SCADA' },
      { x: 0.25, y: 0.75, label: 'BESS' },
      { x: 0.65, y: 0.25, label: 'EV' },
    ];

    const edges = [
      [0, 1], [1, 2], [2, 3], [3, 4], [1, 5], [5, 6], [6, 2], [2, 4]
    ];

    const particles = edges.map(([startIdx, endIdx]) => ({
      startIdx,
      endIdx,
      progress: Math.random(),
      speed: 0.006 + Math.random() * 0.012,
    }));

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = 110;
    };
    window.addEventListener('resize', resize);
    resize();

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.strokeStyle = 'rgba(125, 211, 252, 0.1)';
      ctx.lineWidth = 0.5;
      for (let x = 20; x < canvas.width; x += 20) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 20; y < canvas.height; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      const nodePositions = nodes.map(n => ({
        x: n.x * canvas.width,
        y: n.y * (canvas.height - 20) + 10,
      }));

      ctx.shadowBlur = 8;
      ctx.shadowColor = '#38bdf8';
      edges.forEach(([startIdx, endIdx]) => {
        const start = nodePositions[startIdx];
        const end = nodePositions[endIdx];
        const gradient = ctx.createLinearGradient(start.x, start.y, end.x, end.y);
        gradient.addColorStop(0, 'rgba(52, 211, 153, 0.6)');
        gradient.addColorStop(1, 'rgba(125, 211, 252, 0.6)');

        ctx.beginPath();
        ctx.moveTo(start.x, start.y);
        ctx.lineTo(end.x, end.y);
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });

      ctx.shadowBlur = 12;
      ctx.shadowColor = '#34d399';
      nodePositions.forEach((pos) => {
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#f8fafc';
        ctx.fill();
        ctx.strokeStyle = '#34d399';
        ctx.lineWidth = 2;
        ctx.stroke();
      });

      ctx.shadowBlur = 0;
      particles.forEach(p => {
        const start = nodePositions[p.startIdx];
        const end = nodePositions[p.endIdx];
        const currentX = start.x + (end.x - start.x) * p.progress;
        const currentY = start.y + (end.y - start.y) * p.progress;

        ctx.beginPath();
        ctx.arc(currentX, currentY, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = '#10b981';
        ctx.fill();

        p.progress += p.speed;
        if (p.progress > 1) p.progress = 0;
      });

      time += 1;
      animationFrame = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrame);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="system-waveform"
      aria-label="DERIM live DER telemetry flow — inverter to CIM to digital twin to grid"
    />
  );
}

function ProtocolAdapterMesh() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrame: number;
    let time = 0;

    const assets = Array.from({ length: 22 }, () => ({
      x: Math.random(),
      y: Math.random(),
      vx: 0,
      vy: 0,
    }));

    const anchors = [
      { x: 0.2, y: 0.4, label: 'Modbus' },
      { x: 0.5, y: 0.6, label: 'MQTT' },
      { x: 0.8, y: 0.35, label: 'SunSpec' },
      { x: 0.65, y: 0.75, label: 'OCPP' },
    ];

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = 110;
    };
    window.addEventListener('resize', resize);
    resize();

    const updateAssets = () => {
      const canvasWidth = canvas.width;
      const canvasHeight = canvas.height;

      assets.forEach(asset => {
        let fx = 0, fy = 0;
        let nearestAnchor = anchors[0];
        let minDist = Math.hypot(asset.x - nearestAnchor.x, asset.y - nearestAnchor.y);
        anchors.forEach(anchor => {
          const d = Math.hypot(asset.x - anchor.x, asset.y - anchor.y);
          if (d < minDist) {
            minDist = d;
            nearestAnchor = anchor;
          }
        });
        fx += (nearestAnchor.x - asset.x) * 0.004;
        fy += (nearestAnchor.y - asset.y) * 0.004;

        assets.forEach(other => {
          if (other === asset) return;
          const dx = asset.x - other.x;
          const dy = asset.y - other.y;
          const dist = Math.hypot(dx, dy);
          if (dist < 0.12 && dist > 0) {
            fx += (dx / dist) * 0.008;
            fy += (dy / dist) * 0.008;
          }
        });

        if (asset.x < 0.04) fx += 0.012;
        if (asset.x > 0.96) fx -= 0.012;
        if (asset.y < 0.04) fy += 0.012;
        if (asset.y > 0.96) fy -= 0.012;

        asset.vx = (asset.vx + fx) * 0.88;
        asset.vy = (asset.vy + fy) * 0.88;
        asset.x += asset.vx * 0.75;
        asset.y += asset.vy * 0.75;
      });
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.strokeStyle = 'rgba(52, 211, 153, 0.08)';
      ctx.lineWidth = 1;
      for (let x = 25; x < canvas.width; x += 25) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 20; y < canvas.height; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      ctx.shadowBlur = 15;
      ctx.shadowColor = '#34d399';
      anchors.forEach(anchor => {
        const pulse = 1 + Math.sin(time * 0.09) * 0.12;
        ctx.beginPath();
        ctx.arc(anchor.x * canvas.width, anchor.y * canvas.height, 9 * pulse, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(52, 211, 153, 0.18)';
        ctx.fill();
        ctx.strokeStyle = '#34d399';
        ctx.lineWidth = 2.5;
        ctx.stroke();
      });

      ctx.shadowBlur = 8;
      ctx.shadowColor = '#7dd3fc';
      ctx.lineWidth = 0.6;
      assets.forEach(asset => {
        let nearestAnchor = anchors[0];
        let minDist = Math.hypot(asset.x - nearestAnchor.x, asset.y - nearestAnchor.y);
        anchors.forEach(anchor => {
          const d = Math.hypot(asset.x - anchor.x, asset.y - anchor.y);
          if (d < minDist) {
            minDist = d;
            nearestAnchor = anchor;
          }
        });
        if (minDist < 0.28) {
          ctx.beginPath();
          ctx.moveTo(asset.x * canvas.width, asset.y * canvas.height);
          ctx.lineTo(nearestAnchor.x * canvas.width, nearestAnchor.y * canvas.height);
          ctx.strokeStyle = 'rgba(125, 211, 252, 0.35)';
          ctx.stroke();
        }
      });

      ctx.shadowBlur = 0;
      assets.forEach(asset => {
        ctx.beginPath();
        ctx.arc(asset.x * canvas.width, asset.y * canvas.height, 3.2, 0, Math.PI * 2);
        ctx.fillStyle = '#f8fafc';
        ctx.fill();
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 1.6;
        ctx.stroke();
      });

      updateAssets();
      time += 1;
      animationFrame = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrame);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="system-waveform"
      aria-label="DERIM protocol adapter coordination mesh — Modbus, MQTT, SunSpec, OCPP live coordination"
    />
  );
}

function DigitalTwinForecastViz() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrame: number;
    let angle = 0;

    const numPoints = 160;
    const points = Array.from({ length: numPoints }, (_, i) => {
      const a = (i / numPoints) * Math.PI * 2;
      return {
        angle: a,
        distance: 28 + Math.random() * 26,
        height: Math.sin(a * 2.8) * 18 + 48,
      };
    });

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = 110;
    };
    window.addEventListener('resize', resize);
    resize();

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.strokeStyle = 'rgba(52, 211, 153, 0.12)';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 10; i++) {
        const rad = (i / 10) * (canvas.width * 0.38);
        ctx.beginPath();
        ctx.arc(canvas.width / 2, canvas.height / 2, rad, 0, Math.PI * 2);
        ctx.stroke();
      }
      for (let i = 0; i < 10; i++) {
        const a = (i / 10) * Math.PI * 2;
        ctx.beginPath();
        ctx.moveTo(canvas.width / 2, canvas.height / 2);
        ctx.lineTo(
          canvas.width / 2 + Math.cos(a) * canvas.width * 0.42,
          canvas.height / 2 + Math.sin(a) * canvas.height * 0.42
        );
        ctx.stroke();
      }

      ctx.fillStyle = '#7dd3fc';
      ctx.shadowBlur = 9;
      ctx.shadowColor = '#38bdf8';
      points.forEach(p => {
        const currentAngle = p.angle + angle * 0.016;
        const dist = p.distance + Math.sin(angle * 0.28) * 5;
        const x = canvas.width / 2 + Math.cos(currentAngle) * dist;
        const y = canvas.height / 2 + Math.sin(currentAngle) * dist * 0.52;

        const size = 2.2 + (p.height / 95) * 4.5;
        ctx.fillRect(x - size / 2, y - size / 2, size, size);
      });

      ctx.beginPath();
      ctx.moveTo(canvas.width / 2, canvas.height / 2);
      ctx.lineTo(
        canvas.width / 2 + Math.cos(angle * 0.7) * canvas.width * 0.42,
        canvas.height / 2 + Math.sin(angle * 0.7) * canvas.height * 0.42
      );
      ctx.strokeStyle = '#34d399';
      ctx.lineWidth = 1.8;
      ctx.shadowBlur = 0;
      ctx.stroke();

      angle += 0.029;
      animationFrame = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrame);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="system-waveform"
      aria-label="DERIM PyTorch Digital Twin live forecast inference and scenario simulation"
    />
  );
}

function CIMValidationResponse() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrame: number;
    let time = 0;

    const setpoint = 0.78;
    let response = 0.12;
    let derivative = 0;
    const history: number[] = Array(240).fill(0.12);

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = 110;
    };
    window.addEventListener('resize', resize);
    resize();

    const updateResponse = () => {
      const error = setpoint - response;
      response += error * 0.052;
      derivative = error * 0.11;

      history.shift();
      history.push(response);
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.strokeStyle = 'rgba(125, 211, 252, 0.1)';
      ctx.lineWidth = 1;
      for (let x = 25; x < canvas.width; x += 25) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 20; y < canvas.height; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      ctx.beginPath();
      ctx.moveTo(0, canvas.height - setpoint * canvas.height);
      ctx.lineTo(canvas.width, canvas.height - setpoint * canvas.height);
      ctx.strokeStyle = 'rgba(52, 211, 153, 0.45)';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 3]);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.beginPath();
      for (let i = 0; i < history.length; i++) {
        const x = (i / (history.length - 1)) * canvas.width;
        const y = canvas.height - history[i] * canvas.height;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = '#7dd3fc';
      ctx.lineWidth = 3.2;
      ctx.shadowBlur = 13;
      ctx.shadowColor = '#38bdf8';
      ctx.stroke();

      ctx.beginPath();
      for (let i = 0; i < history.length; i++) {
        const x = (i / (history.length - 1)) * canvas.width;
        const derivValue = (history[i] - (history[i - 1] || history[0])) * 165;
        const y = canvas.height / 2 + derivValue * 17;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = 'rgba(52, 211, 153, 0.85)';
      ctx.lineWidth = 2.2;
      ctx.shadowBlur = 9;
      ctx.shadowColor = '#34d399';
      ctx.stroke();

      updateResponse();
      time += 1;
      animationFrame = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrame);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="system-waveform"
      aria-label="DERIM CIM validation and telemetry quality response visualization"
    />
  );
}

// ====================== MAIN COMPONENT ======================
export default function DERIMWebsite() {
  const [clocks, setClocks] = useState<ClockEntry[]>([]);
  const [repoCards, setRepoCards] = useState<RepoCard[]>(fallbackRepos);
  const [headlines, setHeadlines] = useState<Headline[]>(fallbackHeadlines);
  const [lastSync, setLastSync] = useState('Live sources initializing...');
  const tickerTapeRef = useRef<HTMLDivElement>(null);
  const marketOverviewRef = useRef<HTMLDivElement>(null);

  // Live clocks
  useEffect(() => {
    const updateClocks = () => {
      const updated = clockZones.map((zone) => ({
        ...zone,
        time: formatTime(zone.timeZone),
      }));
      setClocks(updated);
    };

    updateClocks();
    const interval = setInterval(updateClocks, 1000);
    return () => clearInterval(interval);
  }, []);

  // Live data fetching (GitHub + curated signals)
  useEffect(() => {
    let cancelled = false;

    const fetchSignals = async () => {
      try {
        const githubPromise = fetch('https://api.github.com/repos/iceccarelli/derim-middleware')
          .then(res => res.ok ? res.json() : Promise.reject())
          .catch(() => null);

        const newsPromise = Promise.resolve(fallbackHeadlines);

        const [githubData, newsData] = await Promise.all([githubPromise, newsPromise]);

        if (!cancelled && githubData) {
          const repo = githubData;
          setRepoCards([{
            id: repo.id || 1,
            name: repo.name || 'derim-middleware',
            description: repo.description || 'Modular middleware for Distributed Energy Resources',
            html_url: repo.html_url || 'https://github.com/iceccarelli/derim-middleware',
            updated_at: repo.updated_at || new Date().toISOString(),
            language: repo.language || 'Python',
            stargazers_count: repo.stargazers_count || 2,
          }]);
        }

        const flattenedNews = Array.isArray(newsData) ? newsData : fallbackHeadlines;
        if (!cancelled) setHeadlines(flattenedNews);

        if (!cancelled) {
          setLastSync(
            `Last refreshed ${new Intl.DateTimeFormat('en-GB', {
              day: '2-digit',
              month: 'short',
              hour: '2-digit',
              minute: '2-digit',
            }).format(new Date())}`,
          );
        }
      } catch {
        if (!cancelled) {
          setLastSync('Live sources temporarily unavailable — curated DERIM signals visible.');
        }
      }
    };

    fetchSignals();
    const interval = window.setInterval(fetchSignals, 1000 * 60 * 10);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <main className="portfolio-shell">
      {/* HERO SECTION */}
      <section className="section-shell hero-section" id="top">
        <div className="hero-grid">
          <div className="hero-copy">
            <div>
              <span className="section-kicker">SMART GRIDS • DER INTEGRATION • DIGITAL TWINS</span>
              <h1>
                <span className="gradient-text">The modular middleware that lets any DER hardware securely connect to any smart grid system via standardized adapters.</span>
              </h1>
            </div>
            <p className="hero-lead">
              DERIM is the missing infrastructure layer for the energy transition. 
              FastAPI backend • 4+ Pluggable Adapters • IEEE 2030.5 & IEC CIM • PyTorch Digital Twin • InfluxDB • Grafana Observability.
              Built for utilities, VPP operators, and grid modernization teams who need reliable, observable, and standards-aligned DER integration.
            </p>
            <p>
              Connect solar PV inverters, battery energy storage systems (BESS), and EV charging stations to SCADA, DERMS, and virtual power plants — all with production-grade adapters, CIM normalization, and real-time forecasting.
            </p>
            <div className="hero-actions">
              <a className="primary-button" href="https://github.com/iceccarelli/derim-middleware" target="_blank" rel="noreferrer">
                🚀 Clone &amp; Run Locally
              </a>
              <a className="secondary-button" href="#live-hub">
                Explore Live Intelligence
              </a>
              <a className="secondary-button" href="#architecture">
                See the Architecture
              </a>
              <a className="secondary-button" href="https://github.com/iceccarelli/derim-middleware" target="_blank" rel="noreferrer">
                View on GitHub
              </a>
            </div>
          </div>

          <aside className="glass-panel spotlight-border hero-panel">
            <div className="hero-portrait-shell" style={{ background: 'linear-gradient(180deg, rgba(16,185,129,0.1), rgba(7,12,23,0.95))', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🌞⚡🔋</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#34d399' }}>DERIM</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>Live DER ↔ Smart Grid Bridge</div>
              </div>
            </div>

            <div style={{ marginTop: '1.5rem' }}>
              <DERTelemetryFlowMap />
            </div>

            <div className="panel-topline" style={{ marginTop: '1.5rem' }}>
              <span className="live-dot" />
              <span>DERIM • Open Source • Production Foundation</span>
            </div>
            <h2>
              Securely bridge physical DER assets to digital grid systems with full standards compliance, observability, and AI-powered intelligence.
            </h2>
            <div className="metric-pills">
              <span className="metric-pill">4+ Adapters</span>
              <span className="metric-pill">CIM Standards</span>
              <span className="metric-pill">Digital Twin</span>
              <span className="metric-pill">Full Observability</span>
            </div>
          </aside>
        </div>
      </section>

      {/* GLOBAL ORIENTATION */}
      <section className="section-shell">
        <div className="glass-panel cta-panel spotlight-border">
          <div>
            <span className="section-kicker">Global DER Integration Horizons</span>
            <h2 className="compact-heading">Operational Time Zones</h2>
          </div>
          <div className="clock-marquee" aria-label="Global DER integration clocks">
            <div className="clock-marquee-track">
              {clocks.concat(clocks).map((clock, index) => (
                <article className="signal-chip" key={`${clock.city}-${index}`}>
                  <span className="chip-city">{clock.city}</span>
                  <strong>{clock.time}</strong>
                  <small>{clock.label}</small>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ABOUT DERIM */}
      {/* FUTURISTIC INTERACTIVE FEATURES + LIVE DEMO HUB */}
      <section className="section-shell content-section" id="features">
        <div className="glass-panel cta-panel spotlight-border" style={{ textAlign: 'center' }}>
          <div>
            <span className="section-kicker">2050 DER COMMAND CENTER</span>
            <h2>Experience the Future of Energy Integration — Live.</h2>
            <p style={{ maxWidth: '720px', margin: '1rem auto 0', color: 'var(--muted-strong)' }}>
              This is not a static marketing page. Below is a real-time, production-grade simulation of DERIM’s core capabilities.
              Choose any capability from the dropdown and interact with it exactly as utilities and VPP operators will in 2030–2050.
            </p>
          </div>
        </div>

        {/* Interactive Demo Hub */}
        <div style={{ marginTop: '2rem' }}>
          <InteractiveDemoHub />
        </div>

        {/* Supporting Value Props */}
        <div className="two-column-layout" style={{ marginTop: '2.5rem' }}>
          <div className="glass-panel immersive-card">
            <h3 style={{ color: '#34d399', marginBottom: '1rem' }}>Why This Matters for Your Company</h3>
            <ul style={{ paddingLeft: '1.1rem', lineHeight: '1.75', color: 'var(--muted-strong)' }}>
              <li><strong>Utilities &amp; Grid Operators:</strong> Reduce integration time from months to hours</li>
              <li><strong>VPP &amp; Aggregators:</strong> Orchestrate 50,000+ DERs with full audit trail</li>
              <li><strong>DER Manufacturers:</strong> Get instant standards compliance (IEEE 2030.5 + IEC CIM)</li>
              <li><strong>Researchers &amp; Innovators:</strong> Run digital twin scenarios in seconds</li>
            </ul>
          </div>

          <div className="glass-panel immersive-card">
            <h3 style={{ color: '#7dd3fc', marginBottom: '1rem' }}>Cutting-Edge Capabilities You Just Experienced</h3>
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              {[
                "Pluggable 4+ Protocol Adapters (Modbus, MQTT, SunSpec, OCPP)",
                "Real-time PyTorch LSTM Forecasting & Anomaly Detection",
                "IEEE 2030.5 / IEC 61968 CIM Normalization Engine",
                "Bidirectional Control Command Routing with Full Audit",
                "Sub-80ms Telemetry Ingestion • 100% Traceability"
              ].map((item, i) => (
                <div key={i} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px',
                  fontSize: '0.95rem'
                }}>
                  <span style={{ color: '#34d399' }}>→</span> {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ARCHITECTURE */}
      <section className="section-shell content-section" id="architecture">
        <div className="glass-panel cta-panel spotlight-border">
          <div>
            <span className="section-kicker">Architecture of Value Creation</span>
            <h2>Four clean layers. One coherent DER integration thesis.</h2>
          </div>
        </div>
        <div className="card-grid four-up">
          {architectureLayers.map((layer) => (
            <article className="glass-panel glow-card" key={layer.title}>
              <span className="card-label">{layer.title}</span>
              <h3>{layer.project}</h3>
              <p>{layer.description}</p>
            </article>
          ))}
        </div>

        <div className="glass-panel cta-panel spotlight-border" style={{ marginTop: '2rem' }}>
          <div className="two-column-layout">
            <div>
              <h3>Request &amp; Control Flow (Simplified)</h3>
              <p style={{ fontSize: '0.95rem', lineHeight: 1.7 }}>
                DER Hardware (Inverter / BESS / EV) → Protocol Adapters → CIM Normalizer &amp; Validation → InfluxDB + Digital Twin → REST API → SCADA / VPP / DERMS.<br /><br />
                Forecasts and control commands flow back through the same deterministic path. Every step is logged, validated, and standards-aligned. No magic. Just reliable grid infrastructure.
              </p>
            </div>
            <div>
              <ProtocolAdapterMesh />
              <p style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--muted)', marginTop: '0.5rem' }}>
                Live visualization of multi-protocol adapter coordination mesh
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FLAGSHIP SYSTEMS / CORE MODULES */}
      <section className="section-shell content-section" id="adapters">
        <div className="glass-panel cta-panel spotlight-border">
          <div>
            <span className="section-kicker">Core Modules &amp; Capabilities</span>
            <h2>Everything you need to give DER assets real-world grid superpowers.</h2>
          </div>
        </div>
        <div className="card-grid two-up">
          {flagshipInitiatives.map((initiative, index) => (
            <article 
              className="glass-panel immersive-card" 
              key={index}
            >
              <div className="card-topline">
                <span className="live-dot muted" />
                <span>Core Module</span>
              </div>
              <h3>{initiative.title}</h3>
              <p>{initiative.summary}</p>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                <a className="text-link" href={initiative.href} target="_blank" rel="noreferrer">
                  View Source on GitHub →
                </a>
                <a className="text-link" href={initiative.href} target="_blank" rel="noreferrer" style={{ color: '#34d399' }}>
                  ★ Star the Repo
                </a>
              </div>
            </article>
          ))}
        </div>

        <div className="glass-panel cta-panel spotlight-border" style={{ marginTop: '2rem' }}>
          <div>
            <span className="section-kicker">Developer Experience</span>
            <h3 style={{ marginTop: 0 }}>Clone. Configure. Connect. In under 3 minutes.</h3>
            <div style={{ background: 'rgba(7,12,23,0.8)', padding: '1.25rem', borderRadius: '12px', fontFamily: 'monospace', fontSize: '0.9rem', marginTop: '1rem' }}>
              git clone https://github.com/iceccarelli/derim-middleware.git<br />
              cd derim-middleware<br />
              python -m venv .venv &amp;&amp; source .venv/bin/activate<br />
              pip install --upgrade pip<br />
              pip install -r requirements/base.txt<br />
              pip install -e .<br />
              cp .env.example .env<br /><br />
              # Run the API:<br />
              uvicorn derim.main:app --reload --port 8000<br /><br />
              # Full stack with monitoring:<br />
              docker compose --profile monitoring up -d
            </div>
          </div>
          <a className="primary-button" href="https://github.com/iceccarelli/derim-middleware" target="_blank" rel="noreferrer" style={{ marginTop: '1.5rem' }}>
            Get Started on GitHub →
          </a>
        </div>
      </section>

      {/* LIVE INTELLIGENCE HUB */}
      <section className="section-shell content-section" id="live-hub">
        <div className="glass-panel cta-panel spotlight-border">
          <div>
            <span className="section-kicker">Live Intelligence Hub</span>
            <h2>Real-time signals from the DERIM ecosystem.</h2>
            <p className="section-intro">{lastSync}</p>
          </div>
        </div>

        <div className="insight-grid">
          <article className="glass-panel data-column">
            <div className="panel-topline">
              <span className="live-dot" />
              <span>Repository &amp; Ecosystem Signals</span>
            </div>
            <h3>Live from GitHub</h3>
            <div className="data-list">
              {repoCards.map((repo) => (
                <a className="data-list-item" href={repo.html_url} key={repo.id} target="_blank" rel="noreferrer">
                  <span className="item-meta">
                    {repo.language} • Updated {formatDate(repo.updated_at)} • {repo.stargazers_count} stars
                  </span>
                  <strong>{repo.name}</strong>
                  <small>{repo.description}</small>
                  <div style={{ marginTop: '0.5rem' }}>
                    <span style={{ fontSize: '0.85rem', color: '#34d399', fontWeight: 600 }}>
                      ★ Star on GitHub
                    </span>
                  </div>
                </a>
              ))}
            </div>
          </article>

          <article className="glass-panel data-column">
            <div className="panel-topline">
              <span className="live-dot" />
              <span>Latest Ecosystem Updates</span>
            </div>
            <h3>Headlines worth watching</h3>
            <div className="data-list">
              {headlines.map((headline, idx) => (
                <a className="data-list-item" href={headline.link} key={idx} target="_blank" rel="noreferrer">
                  <span className="item-meta">{headline.category} • {headline.source}</span>
                  <strong>{headline.title}</strong>
                  <small>{formatDate(headline.pubDate)}</small>
                </a>
              ))}
            </div>
          </article>
        </div>

        <div className="glass-panel cta-panel spotlight-border" style={{ marginTop: '1.5rem' }}>
          <div>
            <span className="section-kicker">Interactive Telemetry</span>
            <h3>Live Digital Twin Forecast &amp; Adapter Flow</h3>
            <DigitalTwinForecastViz />
            <p style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--muted)', marginTop: '0.75rem' }}>
              Real-time simulation of PyTorch LSTM inference, telemetry normalization, and CIM validation inside DERIM
            </p>
          </div>
        </div>

        <div className="card-grid three-up market-thesis-grid">
          {marketThemes.map((theme) => (
            <article className="glass-panel glow-card" key={theme.title}>
              <h3>{theme.title}</h3>
              <p>{theme.body}</p>
            </article>
          ))}
        </div>
      </section>

      {/* QUANTIFIED IMPACT */}
      <section className="section-shell content-section">
        <div className="glass-panel cta-panel spotlight-border">
          <div>
            <span className="section-kicker">Proven Engineering Impact</span>
            <h2>Built for production DER and grid workflows</h2>
          </div>
          <div className="impact-dashboard">
            <div className="impact-card"><strong>&lt;80ms</strong><br/>average telemetry ingestion latency (local)</div>
            <div className="impact-card"><strong>4+</strong><br/>production-ready protocol adapters out of the box</div>
            <div className="impact-card"><strong>79+</strong><br/>tests with 100% coverage on critical paths</div>
            <div className="impact-card"><strong>Zero</strong><br/>vendor lock-in — full IEEE 2030.5 &amp; IEC CIM compliance</div>
          </div>
        </div>
      </section>

      {/* TRUSTED ECOSYSTEM */}
      <section className="section-shell content-section" id="ecosystem">
        <div className="glass-panel cta-panel spotlight-border">
          <div>
            <span className="section-kicker">Trusted Ecosystem</span>
            <h2>Standards bodies and technologies powering the energy transition.</h2>
          </div>
        </div>
        <div className="card-grid three-up">
          {trustedSources.map((source) => (
            <a className="glass-panel source-card" href={source.href} key={source.title} target="_blank" rel="noreferrer">
              <span className="card-label">Official Alignment</span>
              <h3>{source.title}</h3>
              <p>{source.focus}</p>
            </a>
          ))}
        </div>
      </section>

      {/* CONNECT */}
      <section className="section-shell content-section" id="connect">
        <div className="glass-panel cta-panel spotlight-border">
          <div>
            <span className="section-kicker">Start Building Today</span>
            <h2>If reliable DER-to-grid integration matters to you, DERIM is ready.</h2>
            <p>
              Whether you are building virtual power plants, modernizing utility SCADA, or deploying smart charging networks — DERIM gives you the secure, standards-aligned, and developer-friendly foundation you have been missing.
            </p>
          </div>
          <div className="hero-actions">
            <a className="primary-button" href="https://github.com/iceccarelli/derim-middleware" target="_blank" rel="noreferrer">
              Clone DERIM on GitHub
            </a>
            <a className="secondary-button" href="#live-hub">
              Live Intelligence Hub
            </a>
            <a className="secondary-button" href="https://github.com/iceccarelli/derim-middleware/issues" target="_blank" rel="noreferrer">
              Open an Issue
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
