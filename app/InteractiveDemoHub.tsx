'use client';

import React, { useState, useEffect } from 'react';

interface DemoMode {
  id: string;
  label: string;
  icon: string;
  description: string;
}

const demoModes: DemoMode[] = [
  {
    id: 'adapter',
    label: 'Live Adapter Connection',
    icon: '🔌',
    description: 'Connect real DER hardware via Modbus, MQTT, SunSpec or OCPP'
  },
  {
    id: 'twin',
    label: 'Digital Twin Forecaster',
    icon: '🧠',
    description: 'Run PyTorch LSTM forecast on live telemetry'
  },
  {
    id: 'cim',
    label: 'CIM Validator',
    icon: '📋',
    description: 'Validate & normalize telemetry to IEEE 2030.5 / IEC CIM'
  },
  {
    id: 'control',
    label: 'Control Command Center',
    icon: '⚡',
    description: 'Send real-time setpoints back to DER assets'
  }
];

export default function InteractiveDemoHub() {
  const [selectedMode, setSelectedMode] = useState('adapter');
  const [isConnected, setIsConnected] = useState(false);
  const [telemetry, setTelemetry] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);
  const [anomalyScore, setAnomalyScore] = useState(0);
  const [controlResult, setControlResult] = useState('');
  const [selectedProtocol, setSelectedProtocol] = useState('Modbus TCP');

  // Simulate live telemetry
  useEffect(() => {
    if (selectedMode === 'twin' || selectedMode === 'control') {
      const interval = setInterval(() => {
        const power = 2450 + Math.random() * 800;
        const newTelemetry = {
          device_id: "INV-7842",
          timestamp: new Date().toISOString(),
          power_kw: parseFloat(power.toFixed(1)),
          voltage: 398 + Math.random() * 4,
          frequency: 49.98 + Math.random() * 0.04,
          temperature: 42 + Math.random() * 8,
        };
        setTelemetry(newTelemetry);

        // Simulate forecast
        const predicted = power * (0.92 + Math.random() * 0.16);
        setForecast({
          predicted_kw: parseFloat(predicted.toFixed(1)),
          confidence: 87 + Math.floor(Math.random() * 9),
          horizon_minutes: 15,
        });

        // Anomaly score
        const score = Math.max(0, Math.min(100, 12 + Math.random() * 18));
        setAnomalyScore(parseFloat(score.toFixed(1)));
      }, 1800);

      return () => clearInterval(interval);
    }
  }, [selectedMode]);

  const handleConnect = () => {
    setIsConnected(true);
    setTimeout(() => {
      setTelemetry({
        device_id: "INV-7842",
        status: "CONNECTED",
        protocol: selectedProtocol,
        last_seen: new Date().toISOString(),
      });
    }, 650);
  };

  const handleValidateCIM = () => {
    const sample = {
      device_id: "BESS-3921",
      power_kw: 1875.4,
      soc_percent: 78.2,
      temperature_c: 31.5,
    };
    
    setTelemetry({
      ...sample,
      cim_normalized: true,
      ieee_2030_5_compliant: true,
      iec_61968_class: "DERDevice",
      validation_status: "PASSED",
    });
  };

  const handleSendControl = () => {
    const commands = [
      "Setpoint 1850 kW accepted ✓",
      "Reactive power 0.95 pu command sent",
      "Battery charge rate reduced to 65%",
      "EV charger curtailed by 40% for 12 min"
    ];
    setControlResult(commands[Math.floor(Math.random() * commands.length)]);
    
    setTimeout(() => {
      setControlResult('');
    }, 4200);
  };

  const currentMode = demoModes.find(m => m.id === selectedMode)!;

  return (
    <div className="glass-panel spotlight-border" style={{ 
      background: 'linear-gradient(145deg, rgba(7,12,23,0.95), rgba(10,18,33,0.88))',
      border: '1px solid rgba(52, 211, 153, 0.3)',
      padding: '2.5rem',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Futuristic Header */}
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <div style={{ 
          display: 'inline-flex', 
          alignItems: 'center', 
          gap: '12px',
          background: 'rgba(52, 211, 153, 0.1)',
          padding: '8px 24px',
          borderRadius: '9999px',
          border: '1px solid rgba(52, 211, 153, 0.3)'
        }}>
          <span style={{ fontSize: '1.5rem' }}>🌌</span>
          <span style={{ 
            fontSize: '1.1rem', 
            fontWeight: 700, 
            letterSpacing: '0.5px',
            color: '#34d399'
          }}>
            2050 DER COMMAND CENTER
          </span>
        </div>
        <h3 style={{ 
          fontSize: '2.1rem', 
          margin: '1rem 0 0.5rem',
          background: 'linear-gradient(90deg, #ffffff, #34d399)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          Live Interactive Demo
        </h3>
        <p style={{ color: 'var(--muted)', maxWidth: '620px', margin: '0 auto' }}>
          Experience the future of distributed energy management. Select a capability below and interact in real time.
        </p>
      </div>

      {/* Futuristic Dropdown */}
      <div style={{ marginBottom: '2rem' }}>
        <label style={{ 
          display: 'block', 
          fontSize: '0.85rem', 
          color: '#7dd3fc', 
          marginBottom: '8px',
          letterSpacing: '0.5px'
        }}>
          SELECT CAPABILITY
        </label>
        
        <div style={{ position: 'relative' }}>
          <select
            value={selectedMode}
            onChange={(e) => {
              setSelectedMode(e.target.value);
              setIsConnected(false);
              setTelemetry(null);
              setForecast(null);
              setAnomalyScore(0);
              setControlResult('');
            }}
            style={{
              width: '100%',
              background: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid rgba(52, 211, 153, 0.4)',
              color: 'white',
              padding: '16px 20px',
              borderRadius: '16px',
              fontSize: '1.05rem',
              fontWeight: 600,
              appearance: 'none',
              cursor: 'pointer',
              boxShadow: '0 0 0 1px rgba(52, 211, 153, 0.2)',
            }}
          >
            {demoModes.map(mode => (
              <option key={mode.id} value={mode.id}>
                {mode.icon} {mode.label}
              </option>
            ))}
          </select>
          
          <div style={{
            position: 'absolute',
            right: '20px',
            top: '50%',
            transform: 'translateY(-50%)',
            pointerEvents: 'none',
            color: '#34d399'
          }}>
            ▼
          </div>
        </div>
      </div>

      {/* Demo Area */}
      <div style={{ 
        minHeight: '420px',
        background: 'rgba(5, 10, 20, 0.6)',
        borderRadius: '20px',
        padding: '2rem',
        border: '1px solid rgba(125, 211, 252, 0.15)',
        position: 'relative'
      }}>
        
        {/* Mode Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '2.8rem' }}>{currentMode.icon}</div>
          <div>
            <div style={{ fontSize: '1.35rem', fontWeight: 700 }}>{currentMode.label}</div>
            <div style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>{currentMode.description}</div>
          </div>
        </div>

        {/* === ADAPTER DEMO === */}
        {selectedMode === 'adapter' && (
          <div>
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ fontSize: '0.85rem', color: '#7dd3fc' }}>CHOOSE PROTOCOL</label>
              <select 
                value={selectedProtocol} 
                onChange={(e) => setSelectedProtocol(e.target.value)}
                style={{ 
                  width: '100%', 
                  marginTop: '8px',
                  padding: '12px 16px',
                  background: 'rgba(15,23,42,0.8)',
                  border: '1px solid rgba(52,211,153,0.3)',
                  borderRadius: '12px',
                  color: 'white'
                }}
              >
                <option>Modbus TCP</option>
                <option>MQTT 5.0</option>
                <option>SunSpec</option>
                <option>OCPP 2.0.1</option>
              </select>
            </div>

            <button 
              onClick={handleConnect}
              disabled={isConnected}
              style={{
                width: '100%',
                padding: '18px',
                background: isConnected ? 'rgba(52,211,153,0.2)' : 'linear-gradient(90deg, #34d399, #10b981)',
                border: 'none',
                borderRadius: '9999px',
                color: 'white',
                fontWeight: 700,
                fontSize: '1.1rem',
                cursor: isConnected ? 'default' : 'pointer',
                transition: 'all 0.3s ease'
              }}
            >
              {isConnected ? '✓ CONNECTED — LIVE TELEMETRY STREAMING' : `CONNECT VIA ${selectedProtocol.toUpperCase()}`}
            </button>

            {telemetry && (
              <div style={{ 
                marginTop: '1.5rem', 
                padding: '1.25rem', 
                background: 'rgba(16, 185, 129, 0.08)',
                borderRadius: '12px',
                border: '1px solid rgba(52, 211, 153, 0.3)'
              }}>
                <div style={{ color: '#34d399', fontWeight: 600, marginBottom: '8px' }}>LIVE STATUS</div>
                <pre style={{ fontSize: '0.85rem', color: '#a5f3fc', margin: 0 }}>
                  {JSON.stringify(telemetry, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* === DIGITAL TWIN DEMO === */}
        {selectedMode === 'twin' && (
          <div>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: '1fr 1fr', 
              gap: '1.5rem',
              marginBottom: '1.5rem'
            }}>
              <div style={{ 
                background: 'rgba(15,23,42,0.7)', 
                padding: '1.25rem', 
                borderRadius: '16px',
                border: '1px solid rgba(52,211,153,0.2)'
              }}>
                <div style={{ fontSize: '0.8rem', color: '#7dd3fc' }}>CURRENT POWER</div>
                <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#34d399' }}>
                  {telemetry?.power_kw || '—'} <span style={{ fontSize: '1rem' }}>kW</span>
                </div>
              </div>
              
              <div style={{ 
                background: 'rgba(15,23,42,0.7)', 
                padding: '1.25rem', 
                borderRadius: '16px',
                border: '1px solid rgba(52,211,153,0.2)'
              }}>
                <div style={{ fontSize: '0.8rem', color: '#7dd3fc' }}>15-MIN FORECAST</div>
                <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#7dd3fc' }}>
                  {forecast?.predicted_kw || '—'} <span style={{ fontSize: '1rem' }}>kW</span>
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  Confidence: {forecast?.confidence || '—'}%
                </div>
              </div>
            </div>

            <div style={{ 
              background: 'rgba(239, 68, 68, 0.08)', 
              padding: '1rem 1.25rem', 
              borderRadius: '12px',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <div style={{ fontSize: '0.85rem', color: '#fca5a5' }}>ANOMALY SCORE</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 700, color: anomalyScore > 25 ? '#f87171' : '#34d399' }}>
                  {anomalyScore || '—'} / 100
                </div>
              </div>
              <div style={{ textAlign: 'right', fontSize: '0.75rem', color: '#64748b' }}>
                {anomalyScore > 25 ? '⚠️ INVESTIGATE' : '✓ NORMAL OPERATION'}
              </div>
            </div>

            <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: '#64748b', textAlign: 'center' }}>
              Live PyTorch LSTM inference • Updated every 1.8s
            </div>
          </div>
        )}

        {/* === CIM VALIDATOR === */}
        {selectedMode === 'cim' && (
          <div>
            <button 
              onClick={handleValidateCIM}
              style={{
                width: '100%',
                padding: '16px',
                background: 'linear-gradient(90deg, #7dd3fc, #38bdf8)',
                color: '#0a111f',
                fontWeight: 700,
                borderRadius: '9999px',
                border: 'none',
                fontSize: '1.05rem',
                cursor: 'pointer'
              }}
            >
              VALIDATE &amp; NORMALIZE SAMPLE TELEMETRY
            </button>

            {telemetry && (
              <div style={{ marginTop: '1.5rem' }}>
                <div style={{ 
                  background: 'rgba(16, 185, 129, 0.1)', 
                  padding: '1.5rem', 
                  borderRadius: '16px',
                  border: '1px solid #34d399'
                }}>
                  <div style={{ color: '#34d399', fontWeight: 700, marginBottom: '1rem' }}>✓ CIM NORMALIZED OUTPUT</div>
                  <pre style={{ 
                    fontSize: '0.82rem', 
                    color: '#a5f3fc', 
                    background: 'rgba(5,10,20,0.6)', 
                    padding: '1rem', 
                    borderRadius: '10px',
                    overflowX: 'auto'
                  }}>
                    {JSON.stringify(telemetry, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}

        {/* === CONTROL COMMAND === */}
        {selectedMode === 'control' && (
          <div>
            <div style={{ 
              background: 'rgba(15,23,42,0.7)', 
              padding: '1.5rem', 
              borderRadius: '16px',
              marginBottom: '1.5rem'
            }}>
              <div style={{ fontSize: '0.9rem', color: '#7dd3fc', marginBottom: '8px' }}>TARGET DEVICE</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>INV-7842 • Solar Inverter</div>
            </div>

            <button 
              onClick={handleSendControl}
              style={{
                width: '100%',
                padding: '18px',
                background: 'linear-gradient(90deg, #f59e0b, #d97706)',
                color: 'white',
                fontWeight: 700,
                fontSize: '1.1rem',
                borderRadius: '9999px',
                border: 'none',
                cursor: 'pointer'
              }}
            >
              SEND CONTROL SETPOINT →
            </button>

            {controlResult && (
              <div style={{ 
                marginTop: '1.25rem',
                padding: '1rem 1.25rem',
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid #f59e0b',
                borderRadius: '12px',
                color: '#fcd34d',
                fontWeight: 600
              }}>
                {controlResult}
              </div>
            )}

            <div style={{ 
              marginTop: '1.5rem', 
              fontSize: '0.75rem', 
              color: '#64748b',
              textAlign: 'center'
            }}>
              Commands are routed through DERIM → Adapter → Physical Asset
            </div>
          </div>
        )}
      </div>

      <div style={{ 
        marginTop: '1.5rem', 
        textAlign: 'center', 
        fontSize: '0.75rem', 
        color: '#64748b' 
      }}>
        This is a real-time simulation of DERIM’s production capabilities • All data is synthetic but architecturally accurate
      </div>
    </div>
  );
}
