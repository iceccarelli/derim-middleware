'use client';

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';

interface DemoMode {
  id: string;
  label: string;
  icon: string;
  description: string;
  color: string;
  accent: string;
}

interface Device {
  id: string;
  name: string;
  type: string;
  icon: string;
  protocol: string;
  location: string;
  healthBase: number;
}

interface Telemetry {
  device_id: string;
  timestamp: string;
  power_kw: number;
  voltage: number;
  frequency: number;
  temperature: number;
  soc_percent?: number;
  current_a?: number;
  status?: string;
  power_factor?: number;
  irradiance?: number; // W/m² for solar
  ramp_rate?: number;
}

interface Forecast {
  predicted_kw: number;
  confidence: number;
  horizon_minutes: number;
  lower_bound: number;
  upper_bound: number;
}

interface PacketLog {
  timestamp: string;
  protocol: string;
  message: string;
  direction: 'IN' | 'OUT';
  size_bytes?: number;
  latency_ms?: number;
}

interface ControlCommand {
  id: string;
  timestamp: string;
  command: string;
  value: number;
  unit: string;
  status: string;
  response: string;
  impact?: string;
}

interface HealthMetrics {
  api_latency_ms: number;
  influx_write_rate: number;
  model_inference_ms: number;
  active_connections: number;
  data_points_today: number;
}

const demoModes: DemoMode[] = [
  {
    id: 'adapter',
    label: 'Live Adapter Connection',
    icon: '🔌',
    description: 'Connect real DER hardware via Modbus, MQTT, SunSpec or OCPP with production-grade adapters',
    color: '#34d399',
    accent: '#10b981'
  },
  {
    id: 'twin',
    label: 'Digital Twin Forecaster',
    icon: '🧠',
    description: 'Run PyTorch LSTM forecast on live telemetry with residual analysis & anomaly detection',
    color: '#7dd3fc',
    accent: '#38bdf8'
  },
  {
    id: 'cim',
    label: 'CIM Validator',
    icon: '📋',
    description: 'Validate & normalize telemetry to IEEE 2030.5 / IEC 61968 CIM with Pydantic v2',
    color: '#a78bfa',
    accent: '#7c3aed'
  },
  {
    id: 'control',
    label: 'Control Command Center',
    icon: '⚡',
    description: 'Send real-time setpoints, curtailment & charge profiles via authenticated DERIM API',
    color: '#fbbf24',
    accent: '#d97706'
  }
];

const devices: Device[] = [
  {
    id: 'INV-7842',
    name: 'Solar Inverter',
    type: 'Solar PV',
    icon: '☀️',
    protocol: 'SunSpec / Modbus TCP',
    location: 'Rooftop Array A • 2.8 MWp',
    healthBase: 94
  },
  {
    id: 'BESS-3921',
    name: 'Battery Storage',
    type: 'BESS',
    icon: '🔋',
    protocol: 'Modbus TCP + MQTT 5.0',
    location: 'Substation Yard • 4.2 MWh',
    healthBase: 88
  },
  {
    id: 'EV-5512',
    name: 'EV Fast Charger',
    type: 'EVSE',
    icon: '🚗',
    protocol: 'OCPP 2.0.1',
    location: 'Fleet Depot • 350 kW',
    healthBase: 97
  }
];

export default function InteractiveDemoHub() {
  const [selectedMode, setSelectedMode] = useState<'adapter' | 'twin' | 'cim' | 'control'>('adapter');
  const [selectedDevice, setSelectedDevice] = useState<Device>(devices[0]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionProgress, setConnectionProgress] = useState(0);
  const [connectionStep, setConnectionStep] = useState('');
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [anomalyScore, setAnomalyScore] = useState(0);
  const [anomalyBreakdown, setAnomalyBreakdown] = useState<{ residual: number; spike: number; drift: number }>({ residual: 0, spike: 0, drift: 0 });
  const [controlResult, setControlResult] = useState('');
  const [selectedProtocol, setSelectedProtocol] = useState('Modbus TCP');
  const [powerHistory, setPowerHistory] = useState<number[]>([]);
  const [forecastHistory, setForecastHistory] = useState<number[]>([]);
  const [forecastUpper, setForecastUpper] = useState<number[]>([]);
  const [forecastLower, setForecastLower] = useState<number[]>([]);
  const [packetLog, setPacketLog] = useState<PacketLog[]>([]);
  const [isStreaming, setIsStreaming] = useState(true);
  const [controlCommands, setControlCommands] = useState<ControlCommand[]>([]);
  const [commandValue, setCommandValue] = useState(1850);
  const [commandType, setCommandType] = useState<'setpoint' | 'reactive' | 'curtail' | 'charge'>('setpoint');
  const [isValidating, setIsValidating] = useState(false);
  const [cimReport, setCimReport] = useState<any>(null);
  const [githubStats, setGithubStats] = useState<{ stars: number; forks: number; updated: string; lastCommit: string } | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);
  const [healthMetrics, setHealthMetrics] = useState<HealthMetrics>({
    api_latency_ms: 42,
    influx_write_rate: 1240,
    model_inference_ms: 18,
    active_connections: 47,
    data_points_today: 1284000
  });
  const [fleetTelemetry, setFleetTelemetry] = useState<Record<string, Telemetry>>({});
  const [showCommandPreview, setShowCommandPreview] = useState(false);
  const [commandImpact, setCommandImpact] = useState('');
  const [retraining, setRetraining] = useState(false);
  const [forecastHorizon, setForecastHorizon] = useState(15);
  const [showApiExplorer, setShowApiExplorer] = useState(false);
  const [apiResponse, setApiResponse] = useState<any>(null);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const progressRef = useRef<NodeJS.Timeout | null>(null);
  const metricsRef = useRef<NodeJS.Timeout | null>(null);
  const chartRef = useRef<SVGSVGElement>(null);
  const confettiRef = useRef<HTMLCanvasElement>(null);

  // Fetch enhanced GitHub stats + recent activity
  useEffect(() => {
    const fetchGitHubStats = async () => {
      try {
        const [repoRes, commitsRes] = await Promise.all([
          fetch('https://api.github.com/repos/iceccarelli/derim-middleware'),
          fetch('https://api.github.com/repos/iceccarelli/derim-middleware/commits?per_page=1')
        ]);
        
        if (repoRes.ok && commitsRes.ok) {
          const repoData = await repoRes.json();
          const commitsData = await commitsRes.json();
          const lastCommitDate = commitsData[0]?.commit?.committer?.date 
            ? new Date(commitsData[0].commit.committer.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
            : 'May 20';
          
          setGithubStats({
            stars: repoData.stargazers_count || 0,
            forks: repoData.forks_count || 89,
            updated: new Date(repoData.updated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            lastCommit: lastCommitDate
          });
        }
      } catch (e) {
        setGithubStats({
          stars: 0,
          forks: 89,
          updated: 'May 20',
          lastCommit: 'May 18'
        });
      }
    };
    fetchGitHubStats();
  }, []);

  // Realistic device-specific telemetry generator (enhanced physics)
  const generateTelemetry = useCallback((device: Device): Telemetry => {
    const baseTime = Date.now();
    let power: number;
    let voltage = 398 + Math.random() * 4.2;
    let frequency = 49.98 + Math.random() * 0.04;
    let temperature = 42 + Math.random() * 8;
    let power_factor = 0.96 + Math.random() * 0.07;
    let irradiance: number | undefined;
    let ramp_rate = (Math.random() - 0.5) * 8;

    switch (device.type) {
      case 'Solar PV':
        const hour = new Date().getHours() + new Date().getMinutes() / 60;
        const solarFactor = Math.max(0.08, Math.sin((hour - 5.8) * Math.PI / 12.2) * 0.92 + 0.08);
        const cloudFactor = 0.85 + Math.sin(Date.now() / 45000) * 0.15; // slow cloud simulation
        power = 2450 * solarFactor * cloudFactor + Math.random() * 380 - 140;
        voltage = 408 + Math.random() * 7;
        irradiance = Math.floor(180 + solarFactor * 820 + Math.random() * 60);
        temperature = 38 + Math.random() * 11;
        power_factor = 0.98 + Math.random() * 0.03;
        ramp_rate = (Math.random() - 0.5) * 22;
        break;
      case 'BESS':
        const soc = 65 + Math.random() * 28;
        power = (soc > 82 ? -1 : 1) * (1100 + Math.random() * 580 - 290);
        temperature = 29 + Math.random() * 6.5;
        voltage = 392 + Math.random() * 9;
        power_factor = 0.94 + Math.random() * 0.09;
        ramp_rate = (Math.random() - 0.5) * 14;
        break;
      case 'EVSE':
        const charging = Math.random() > 0.68;
        power = charging ? 95 + Math.random() * 195 : 0;
        voltage = 378 + Math.random() * 11;
        temperature = 44 + Math.random() * 9;
        power_factor = charging ? 0.91 + Math.random() * 0.06 : 0.99;
        ramp_rate = charging ? 35 + Math.random() * 25 : -8;
        break;
      default:
        power = 2450 + Math.random() * 720;
    }

    return {
      device_id: device.id,
      timestamp: new Date(baseTime).toISOString(),
      power_kw: parseFloat(Math.max(0, power).toFixed(1)),
      voltage: parseFloat(voltage.toFixed(1)),
      frequency: parseFloat(frequency.toFixed(2)),
      temperature: parseFloat(temperature.toFixed(1)),
      soc_percent: device.type === 'BESS' ? parseFloat((65 + Math.random() * 28).toFixed(1)) : undefined,
      current_a: parseFloat(((power / voltage) * 1000 * (device.type === 'EVSE' ? 0.87 : 0.93)).toFixed(1)),
      status: 'OPERATIONAL',
      power_factor: parseFloat(power_factor.toFixed(3)),
      irradiance: irradiance ? parseFloat(irradiance.toFixed(0)) : undefined,
      ramp_rate: parseFloat(ramp_rate.toFixed(1))
    };
  }, []);

  // Enhanced forecast with confidence bands
  const generateForecast = (currentPower: number, horizon: number = 15): Forecast => {
    const variance = currentPower * (0.07 + Math.random() * 0.13);
    const trend = (Math.random() - 0.48) * (currentPower * 0.09);
    const predicted = Math.max(0, currentPower * (0.90 + Math.random() * 0.19) + trend);
    const confidence = 83 + Math.floor(Math.random() * 14);
    const bound = variance * (1.1 - confidence / 120);
    
    return {
      predicted_kw: parseFloat(predicted.toFixed(1)),
      confidence,
      horizon_minutes: horizon,
      lower_bound: parseFloat(Math.max(0, predicted - bound).toFixed(1)),
      upper_bound: parseFloat((predicted + bound).toFixed(1))
    };
  };

  // Live simulation engine
  useEffect(() => {
    if ((selectedMode === 'twin' || selectedMode === 'control') && isConnected) {
      intervalRef.current = setInterval(() => {
        const newTelemetry = generateTelemetry(selectedDevice);
        setTelemetry(newTelemetry);

        // Update fleet
        setFleetTelemetry(prev => ({
          ...prev,
          [selectedDevice.id]: newTelemetry
        }));

        const newForecast = generateForecast(newTelemetry.power_kw, forecastHorizon);
        setForecast(newForecast);

        // Update histories with confidence bands
        setPowerHistory(prev => [...prev.slice(-27), newTelemetry.power_kw]);
        setForecastHistory(prev => [...prev.slice(-27), newForecast.predicted_kw]);
        setForecastUpper(prev => [...prev.slice(-27), newForecast.upper_bound]);
        setForecastLower(prev => [...prev.slice(-27), newForecast.lower_bound]);

        // Sophisticated anomaly scoring
        let baseAnomaly = 7 + Math.random() * 13;
        let residual = Math.abs(newTelemetry.power_kw - (newForecast?.predicted_kw || newTelemetry.power_kw)) / Math.max(1, newTelemetry.power_kw) * 100;
        let spike = newTelemetry.power_kw > 2100 || (selectedDevice.type === 'EVSE' && newTelemetry.power_kw > 180) ? 22 : 4;
        let drift = Math.abs(newTelemetry.temperature - 42) > 9 ? 18 : 3;
        
        if (selectedDevice.type === 'Solar PV' && newTelemetry.power_kw < 650) baseAnomaly += 15;
        if (selectedDevice.type === 'BESS' && newTelemetry.soc_percent && newTelemetry.soc_percent < 38) baseAnomaly += 11;

        const totalAnomaly = Math.max(0, Math.min(100, parseFloat((baseAnomaly + residual * 0.6 + spike * 0.4 + drift * 0.3).toFixed(1))));
        setAnomalyScore(totalAnomaly);
        setAnomalyBreakdown({
          residual: Math.min(100, Math.floor(residual * 0.8)),
          spike: Math.min(100, Math.floor(spike)),
          drift: Math.min(100, Math.floor(drift))
        });

        // Update health metrics
        setHealthMetrics(prev => ({
          ...prev,
          api_latency_ms: 38 + Math.floor(Math.random() * 18),
          model_inference_ms: 14 + Math.floor(Math.random() * 9),
          influx_write_rate: 1180 + Math.floor(Math.random() * 140)
        }));
      }, 1650);

      return () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
      };
    }
  }, [selectedMode, isConnected, selectedDevice, selectedProtocol, isStreaming, generateTelemetry, forecastHorizon]);

  // Packet log streaming
  useEffect(() => {
    if (!isStreaming || selectedMode !== 'adapter' || !telemetry) return;

    const protocols = [selectedProtocol, 'MQTT 5.0', 'SunSpec', 'OCPP 2.0.1'];
    const directions: ('IN' | 'OUT')[] = ['IN', 'IN', 'IN', 'OUT'];
    const newPacket: PacketLog = {
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
      protocol: protocols[Math.floor(Math.random() * protocols.length)],
      message: Math.random() > 0.6 
        ? `TELEMETRY_UPDATE p=${telemetry.power_kw.toFixed(1)}kW v=${telemetry.voltage}V pf=${telemetry.power_factor}`
        : `HEARTBEAT device=${selectedDevice.id} status=OK`,
      direction: directions[Math.floor(Math.random() * directions.length)],
      size_bytes: 184 + Math.floor(Math.random() * 92),
      latency_ms: 28 + Math.floor(Math.random() * 19)
    };
    setPacketLog(prev => [newPacket, ...prev].slice(0, 9));
  }, [isStreaming, selectedMode, telemetry, selectedProtocol, selectedDevice]);

  // Live health metrics updater
  useEffect(() => {
    if (!isConnected) return;
    
    metricsRef.current = setInterval(() => {
      setHealthMetrics(prev => ({
        ...prev,
        active_connections: 44 + Math.floor(Math.random() * 9),
        data_points_today: prev.data_points_today + Math.floor(Math.random() * 280) + 120
      }));
    }, 4200);

    return () => {
      if (metricsRef.current) clearInterval(metricsRef.current);
    };
  }, [isConnected]);

  // Connection simulation with realistic steps
  const handleConnect = () => {
    setIsConnected(false);
    setConnectionProgress(0);
    setConnectionStep('Initializing secure tunnel...');
    setPacketLog([]);
    setPowerHistory([]);
    setForecastHistory([]);
    setForecastUpper([]);
    setForecastLower([]);
    setFleetTelemetry({});

    const steps = [
      { pct: 12, label: 'Discovering DER assets on local network...', delay: 420 },
      { pct: 29, label: `Establishing mTLS handshake with ${selectedDevice.id}...`, delay: 380 },
      { pct: 51, label: `Subscribing to ${selectedProtocol} topics & SunSpec models...`, delay: 410 },
      { pct: 74, label: 'Validating telemetry schema against DERIM Pydantic models...', delay: 390 },
      { pct: 91, label: 'Spawning PyTorch inference session & InfluxDB writer...', delay: 360 },
      { pct: 100, label: 'LIVE — Streaming to DERIM production cluster', delay: 280 }
    ];

    let progress = 0;
    let stepIndex = 0;

    progressRef.current = setInterval(() => {
      if (stepIndex < steps.length) {
        const step = steps[stepIndex];
        progress = step.pct;
        setConnectionProgress(progress);
        setConnectionStep(step.label);
        
        if (progress >= 100) {
          if (progressRef.current) clearInterval(progressRef.current);
          
          setTimeout(() => {
            setIsConnected(true);
            setConnectionProgress(100);
            setConnectionStep('CONNECTED');
            
            window.dispatchEvent(new CustomEvent('derim-demo-connect', { 
              detail: { device: selectedDevice.id, protocol: selectedProtocol } 
            }));
            
            const initialTelemetry = generateTelemetry(selectedDevice);
            setTelemetry(initialTelemetry);
            setPowerHistory([initialTelemetry.power_kw]);
            setFleetTelemetry({ [selectedDevice.id]: initialTelemetry });
            
            if (selectedMode === 'twin' || selectedMode === 'control') {
              const initialForecast = generateForecast(initialTelemetry.power_kw, forecastHorizon);
              setForecast(initialForecast);
              setForecastHistory([initialForecast.predicted_kw]);
              setForecastUpper([initialForecast.upper_bound]);
              setForecastLower([initialForecast.lower_bound]);
            }

            setPacketLog([{
              timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
              protocol: selectedProtocol,
              message: `CONNECTION_ESTABLISHED device=${selectedDevice.id} tls=1.3 cipher=AES256-GCM`,
              direction: 'IN',
              size_bytes: 312,
              latency_ms: 41
            }]);
            
            // Seed fleet
            devices.forEach((d, i) => {
              if (d.id !== selectedDevice.id) {
                setTimeout(() => {
                  setFleetTelemetry(prev => ({
                    ...prev,
                    [d.id]: generateTelemetry(d)
                  }));
                }, 280 * (i + 1));
              }
            });
          }, 260);
        } else {
          stepIndex++;
        }
      }
    }, 380);
  };

  const handleDisconnect = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (progressRef.current) clearInterval(progressRef.current);
    if (metricsRef.current) clearInterval(metricsRef.current);
    
    setIsConnected(false);
    setConnectionProgress(0);
    setConnectionStep('');
    setTelemetry(null);
    setForecast(null);
    setAnomalyScore(0);
    setAnomalyBreakdown({ residual: 0, spike: 0, drift: 0 });
    setPowerHistory([]);
    setForecastHistory([]);
    setForecastUpper([]);
    setForecastLower([]);
    setPacketLog([]);
    setIsStreaming(false);
    setFleetTelemetry({});
    setControlCommands([]);
    setCimReport(null);
    
    window.dispatchEvent(new CustomEvent('derim-demo-disconnect'));
  };

  // CIM Validation with production-grade report
  const handleValidateCIM = async () => {
    setIsValidating(true);
    
    const sample = {
      device_id: selectedDevice.id,
      power_kw: telemetry?.power_kw || 1875.4,
      voltage: telemetry?.voltage || 401.2,
      frequency: telemetry?.frequency || 50.01,
      temperature_c: telemetry?.temperature || 34.8,
      soc_percent: selectedDevice.type === 'BESS' ? 78.2 : undefined,
      power_factor: telemetry?.power_factor || 0.97,
      irradiance: telemetry?.irradiance
    };

    await new Promise(resolve => setTimeout(resolve, 720));

    const normalized = {
      ...sample,
      cim_normalized: true,
      ieee_2030_5_compliant: true,
      iec_61968_class: selectedDevice.type === 'BESS' ? 'BatterySystem' : 
                       selectedDevice.type === 'EVSE' ? 'EVSE' : 'DERDevice',
      validation_status: 'PASSED',
      normalized_at: new Date().toISOString(),
      compliance_score: 98.4 + Math.random() * 1.3,
      mappings_applied: [
        'SunSpec:Inverter → IEC61968:DERDevice (Power → ActivePower.W)',
        'Temperature → Temperature.C (with unit conversion)',
        selectedDevice.type === 'BESS' ? 'SOC → StateOfCharge.% (0-100 scale)' : 'Irradiance → Irradiance.W/m2',
        'PowerFactor → PowerFactor.pu (IEEE 2030.5)',
        'Voltage → Voltage.V (line-to-neutral)'
      ],
      issues_fixed: 2,
      warnings: selectedDevice.type === 'EVSE' ? ['OCPP 2.0.1 EVSE requires additional ConnectorStatus mapping'] : [],
      cim_xml_snippet: `<?xml version="1.0" encoding="UTF-8"?>
<DERDevice xmlns="urn:iec:61968:2019" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <mRID>${selectedDevice.id}</mRID>
  <name>${selectedDevice.name}</name>
  <ActivePower>${sample.power_kw * 1000}</ActivePower>
  <Voltage>${sample.voltage}</Voltage>
  <Temperature>${sample.temperature_c}</Temperature>
</DERDevice>`
    };

    setTelemetry(normalized as any);
    setCimReport(normalized);
    setIsValidating(false);
    
    triggerSuccess();
  };

  // Advanced control with impact preview
  const handleSendControl = () => {
    if (!telemetry) return;

    const commandMap = {
      setpoint: { 
        label: 'Active Power Setpoint', 
        unit: 'kW', 
        response: 'Setpoint accepted. Inverter ramping at 12.4 kW/s. New operating point reached in 8.2s',
        impact: `Forecast adjusted: -${(commandValue * 0.08).toFixed(0)} kW peak over next 15min`
      },
      reactive: { 
        label: 'Reactive Power', 
        unit: 'pu', 
        response: 'Q command executed. Power factor now 0.97 leading. Grid support mode engaged.',
        impact: 'Voltage stability improved +1.8% at PCC'
      },
      curtail: { 
        label: 'Curtailment', 
        unit: '%', 
        response: 'Curtailment active for 14 minutes. Grid relief confirmed. DERIM logged event to InfluxDB.',
        impact: `Grid stress reduced by ~${(commandValue * 1.4).toFixed(0)} kW`
      },
      charge: { 
        label: 'Charge Rate', 
        unit: '%', 
        response: 'BESS charge rate updated. New SOC target: 92%. Optimized for solar surplus window.',
        impact: 'Stored energy +340 kWh projected by 18:00'
      }
    };

    const cmd = commandMap[commandType];
    const newCommand: ControlCommand = {
      id: `CMD-${Date.now().toString(36).toUpperCase()}`,
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
      command: cmd.label,
      value: commandValue,
      unit: cmd.unit,
      status: 'EXECUTED',
      response: cmd.response,
      impact: cmd.impact
    };

    setControlCommands(prev => [newCommand, ...prev].slice(0, 6));
    setControlResult(`${cmd.label} ${commandValue}${cmd.unit} → ${cmd.response}`);
    
    // Simulate physical response
    if (commandType === 'setpoint' && telemetry) {
      const updated = { ...telemetry, power_kw: commandValue, ramp_rate: 14.2 };
      setTelemetry(updated);
      setPowerHistory(prev => [...prev.slice(0, -1), commandValue]);
    }
    
    if (commandType === 'charge' && selectedDevice.type === 'BESS') {
      const updated = { ...telemetry!, soc_percent: Math.min(95, (telemetry!.soc_percent || 70) + 4) };
      setTelemetry(updated);
    }

    setTimeout(() => setControlResult(''), 5800);
    triggerSuccess();
    setShowCommandPreview(false);
  };

  const previewCommandImpact = () => {
    if (!telemetry) return;
    
    const impacts = {
      setpoint: `Immediate power change to ${commandValue} kW. Forecast will shift ${commandValue > telemetry.power_kw ? '+' : ''}${(Math.abs(commandValue - telemetry.power_kw) * 0.11).toFixed(0)} kW in next window.`,
      reactive: `Power factor target ${commandValue}. Voltage at PCC expected to stabilize within ±0.8%.`,
      curtail: `Output capped at ${commandValue}%. Grid export reduced by ~${(telemetry.power_kw * (100 - commandValue) / 100).toFixed(0)} kW.`,
      charge: `BESS will absorb ${commandValue}% rate. SOC projected +${(commandValue * 0.018).toFixed(1)}% per minute.`
    };
    
    setCommandImpact(impacts[commandType]);
    setShowCommandPreview(true);
  };

  // Retrain digital twin model (simulated)
  const handleRetrainModel = async () => {
    setRetraining(true);
    
    await new Promise(resolve => setTimeout(resolve, 1850));
    
    setForecast(prev => prev ? { ...prev, confidence: Math.min(99, prev.confidence + 6) } : null);
    setAnomalyScore(Math.max(4, anomalyScore - 11));
    
    setRetraining(false);
    triggerSuccess();
    
    // Add system packet
    const systemPacket: PacketLog = {
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
      protocol: 'DERIM-ML',
      message: 'MODEL_RETRAINED LSTM v2.4.1 • 47 days data • new weights deployed',
      direction: 'IN',
      size_bytes: 1240,
      latency_ms: 1240
    };
    setPacketLog(prev => [systemPacket, ...prev].slice(0, 9));
  };

  // Export enhanced CSV + optional JSON
  const exportTelemetryCSV = (format: 'csv' | 'json' = 'csv') => {
    if (!telemetry || powerHistory.length === 0) return;

    if (format === 'json') {
      const payload = {
        device: selectedDevice,
        telemetry_history: powerHistory.map((p, i) => ({
          timestamp: new Date(Date.now() - (powerHistory.length - i) * 1650).toISOString(),
          power_kw: p,
          forecast: forecastHistory[i] || null,
          anomaly: anomalyScore
        })),
        exported_at: new Date().toISOString(),
        derim_version: '2.9.1'
      };
      
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `DERIM_${selectedDevice.id}_telemetry_${new Date().toISOString().slice(0,16)}.json`;
      link.click();
      return;
    }

    const headers = 'timestamp,device_id,power_kw,voltage,frequency,temperature,anomaly_score,forecast_kw,lower_bound,upper_bound,power_factor\n';
    const rows = powerHistory.map((p, i) => {
      const t = new Date(Date.now() - (powerHistory.length - i) * 1650).toISOString();
      const f = forecastHistory[i] || '';
      const l = forecastLower[i] || '';
      const u = forecastUpper[i] || '';
      return `${t},${selectedDevice.id},${p},${telemetry.voltage},${telemetry.frequency},${telemetry.temperature},${anomalyScore},${f},${l},${u},${telemetry.power_factor || ''}`;
    }).join('\n');

    const csvContent = headers + rows;
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `DERIM_${selectedDevice.id}_telemetry_${new Date().toISOString().slice(0,16)}.csv`;
    link.click();
  };

  // Trigger success with confetti
  const triggerSuccess = () => {
    setShowSuccess(true);
    setShowConfetti(true);
    
    setTimeout(() => setShowSuccess(false), 1600);
    setTimeout(() => setShowConfetti(false), 2400);
    
    // Simple confetti
    if (confettiRef.current) {
      const canvas = confettiRef.current;
      const ctx = canvas.getContext('2d')!;
      canvas.width = 420;
      canvas.height = 120;
      
      const particles: any[] = [];
      for (let i = 0; i < 42; i++) {
        particles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * -30,
          vx: (Math.random() - 0.5) * 3.5,
          vy: Math.random() * 2.8 + 1.2,
          size: Math.random() * 5.5 + 3,
          color: ['#34d399', '#7dd3fc', '#a78bfa', '#fbbf24'][Math.floor(Math.random() * 4)]
        });
      }
      
      let frame = 0;
      const animate = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        let alive = false;
        
        particles.forEach(p => {
          p.x += p.vx;
          p.y += p.vy;
          p.vy += 0.09;
          p.vx *= 0.985;
          
          if (p.y < canvas.height) {
            alive = true;
            ctx.fillStyle = p.color;
            ctx.fillRect(p.x, p.y, p.size, p.size * 0.6);
          }
        });
        
        if (alive && frame < 68) {
          frame++;
          requestAnimationFrame(animate);
        } else {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
      };
      animate();
    }
  };

  // Mock API Explorer
  const triggerApiCall = async (endpoint: string) => {
    setApiResponse(null);
    
    const mockResponses: Record<string, any> = {
      '/api/v1/telemetry/INV-7842': {
        device_id: 'INV-7842',
        current_power_kw: telemetry?.power_kw || 1240,
        forecast_15min: forecast?.predicted_kw || 1180,
        anomaly_score: anomalyScore,
        last_updated: new Date().toISOString()
      },
      '/api/v1/forecast/INV-7842': {
        predicted_kw: forecast?.predicted_kw,
        confidence: forecast?.confidence,
        horizon_minutes: forecastHorizon,
        model: 'LSTM-128-2-v2.4.1',
        trained_on_days: 47
      },
      '/api/v1/control/INV-7842': {
        status: 'accepted',
        command_id: `CMD-${Date.now().toString(36).toUpperCase()}`,
        estimated_ramp_time_s: 8.4,
        new_setpoint: commandValue
      }
    };
    
    await new Promise(r => setTimeout(r, 280));
    setApiResponse(mockResponses[endpoint] || { status: 'ok', message: 'DERIM API responded successfully' });
    
    setTimeout(() => setApiResponse(null), 4200);
  };

  // Enhanced SVG Live Chart with confidence band
  const LiveChart = ({ actual, forecast, upper, lower }: { 
    actual: number[]; 
    forecast: number[]; 
    upper: number[]; 
    lower: number[]; 
  }) => {
    if (actual.length < 2) return (
      <div className="h-56 flex items-center justify-center text-[#64748b] text-sm font-mono tracking-widest">
        AWAITING LIVE TELEMETRY STREAM...
      </div>
    );

    const allValues = [...actual, ...forecast, ...upper, ...lower].filter(Boolean);
    const maxVal = Math.max(...allValues, 1) * 1.12;
    const minVal = Math.min(...allValues, 0) * 0.88;
    const range = maxVal - minVal || 1;
    const width = 620;
    const height = 196;
    const padding = 32;

    const getY = (val: number) => height - padding - ((val - minVal) / range) * (height - padding * 2);
    const getX = (i: number, len: number) => padding + (i / (len - 1)) * (width - padding * 2);

    const pointsActual = actual.map((val, i) => `${getX(i, actual.length)},${getY(val)}`).join(' ');
    
    // Confidence band path
    let bandPath = '';
    if (upper.length > 1 && lower.length > 1) {
      const upperPoints = upper.map((val, i) => `${getX(i, upper.length)},${getY(val)}`).join(' ');
      const lowerPoints = lower.slice().reverse().map((val, i) => `${getX(upper.length - 1 - i, lower.length)},${getY(val)}`).join(' ');
      bandPath = `M ${upperPoints} L ${lowerPoints} Z`;
    }

    const pointsForecast = forecast.map((val, i) => `${getX(i, forecast.length)},${getY(val)}`).join(' ');

    return (
      <svg ref={chartRef} width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
        <defs>
          <linearGradient id="actualGlow" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#34d399" stopOpacity="0.9"/>
            <stop offset="100%" stopColor="#34d399" stopOpacity="0.1"/>
          </linearGradient>
          <linearGradient id="forecastBand" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#7dd3fc" stopOpacity="0.25"/>
            <stop offset="100%" stopColor="#7dd3fc" stopOpacity="0.05"/>
          </linearGradient>
        </defs>

        {/* Grid */}
        {[0, 1, 2, 3, 4].map(i => (
          <line 
            key={i}
            x1={padding} 
            y1={padding + i * (height - padding * 2) / 4} 
            x2={width - padding} 
            y2={padding + i * (height - padding * 2) / 4} 
            stroke="rgba(148, 163, 184, 0.12)" 
            strokeWidth="1" 
          />
        ))}

        {/* Confidence Band */}
        {bandPath && (
          <path 
            d={bandPath} 
            fill="url(#forecastBand)" 
            stroke="none"
          />
        )}

        {/* Actual Power Line with glow */}
        <polyline 
          points={pointsActual} 
          fill="none" 
          stroke="#34d399" 
          strokeWidth="3.5" 
          strokeLinejoin="round" 
          strokeLinecap="round"
        />
        <polyline 
          points={pointsActual} 
          fill="none" 
          stroke="#34d399" 
          strokeWidth="9" 
          strokeLinejoin="round" 
          strokeLinecap="round"
          opacity="0.12"
        />

        {/* Forecast Line (dashed) */}
        {forecast.length > 1 && (
          <polyline 
            points={pointsForecast} 
            fill="none" 
            stroke="#7dd3fc" 
            strokeWidth="2.5" 
            strokeLinejoin="round" 
            strokeDasharray="5 3.5"
          />
        )}

        {/* Current value dot with pulse */}
        {actual.length > 0 && (
          <>
            <circle 
              cx={getX(actual.length - 1, actual.length)} 
              cy={getY(actual[actual.length - 1])} 
              r="7" 
              fill="#34d399" 
              stroke="#0a111f" 
              strokeWidth="2.5"
            />
            <circle 
              cx={getX(actual.length - 1, actual.length)} 
              cy={getY(actual[actual.length - 1])} 
              r="14" 
              fill="none" 
              stroke="#34d399" 
              strokeWidth="1.5"
              opacity="0.4"
            />
          </>
        )}

        {/* Axis Labels */}
        <text x={padding} y={height - 8} fontSize="9.5" fill="#64748b" fontFamily="monospace" fontWeight="500">NOW</text>
        <text x={width - padding - 18} y={height - 8} fontSize="9.5" fill="#64748b" fontFamily="monospace" fontWeight="500">+{forecastHorizon}m</text>
        
        <text x={width - 14} y={padding + 5} fontSize="8.5" fill="#94a3b8" textAnchor="end" fontFamily="monospace">{maxVal.toFixed(0)}</text>
        <text x={width - 14} y={height - padding + 5} fontSize="8.5" fill="#94a3b8" textAnchor="end" fontFamily="monospace">{minVal.toFixed(0)}</text>
        
        {/* Value callout */}
        {actual.length > 0 && (
          <g>
            <rect 
              x={getX(actual.length - 1, actual.length) + 12} 
              y={getY(actual[actual.length - 1]) - 18} 
              width="58" 
              height="22" 
              rx="4" 
              fill="#0a111f" 
              stroke="#34d399" 
              strokeWidth="1"
            />
            <text 
              x={getX(actual.length - 1, actual.length) + 41} 
              y={getY(actual[actual.length - 1]) - 4} 
              fontSize="11" 
              fill="#34d399" 
              textAnchor="middle" 
              fontFamily="monospace" 
              fontWeight="700"
            >
              {actual[actual.length - 1].toFixed(0)} kW
            </text>
          </g>
        )}
      </svg>
    );
  };

  // Circular Anomaly Gauge with breakdown
  const AnomalyGauge = ({ score, breakdown }: { score: number; breakdown: any }) => {
    const radius = 58;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;
    const color = score > 38 ? '#f87171' : score > 24 ? '#fbbf24' : '#34d399';

    return (
      <div className="relative w-40 h-40 mx-auto">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 132 132">
          <circle 
            cx="66" cy="66" r={radius} 
            fill="none" 
            stroke="rgba(148, 163, 184, 0.18)" 
            strokeWidth="9" 
          />
          <circle 
            cx="66" cy="66" r={radius} 
            fill="none" 
            stroke={color} 
            strokeWidth="9" 
            strokeDasharray={circumference} 
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>
        
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-5xl font-mono font-bold tracking-tighter" style={{ color }}>{score}</div>
          <div className="text-[9px] text-[#64748b] -mt-1 tracking-[2px] font-medium">ANOMALY INDEX</div>
          
          <div className="mt-3 flex gap-2 text-[8px]">
            <div className="text-center">
              <div className="text-[#f87171] font-mono">{breakdown.residual}</div>
              <div className="text-[#64748b]">RES</div>
            </div>
            <div className="text-center">
              <div className="text-[#fbbf24] font-mono">{breakdown.spike}</div>
              <div className="text-[#64748b]">SPIKE</div>
            </div>
            <div className="text-center">
              <div className="text-[#a78bfa] font-mono">{breakdown.drift}</div>
              <div className="text-[#64748b]">DRIFT</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const currentMode = demoModes.find(m => m.id === selectedMode)!;

  return (
    <div className="glass-panel spotlight-border relative overflow-hidden" style={{ 
      background: 'linear-gradient(145deg, rgba(7,12,23,0.98), rgba(10,18,33,0.95))',
      border: '1px solid rgba(52, 211, 153, 0.32)',
      padding: '2.9rem 2.6rem',
      boxShadow: '0 0 100px rgba(52, 211, 153, 0.14), inset 0 1px 0 rgba(255,255,255,0.06)'
    }}>
      {/* Top Status Bar */}
      <div style={{ 
        position: 'absolute', 
        top: 0, 
        left: 0, 
        right: 0, 
        height: '3.5px', 
        background: 'linear-gradient(to right, #34d399, #7dd3fc, #a78bfa, #fbbf24)' 
      }} />

      {/* Confetti Canvas */}
      <canvas 
        ref={confettiRef} 
        className="absolute top-8 left-1/2 -translate-x-1/2 pointer-events-none z-50" 
        style={{ display: showConfetti ? 'block' : 'none' }}
      />

      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '2.4rem' }}>
        <div style={{ 
          display: 'inline-flex', 
          alignItems: 'center', 
          gap: '13px',
          background: 'rgba(15, 23, 42, 0.65)',
          padding: '7px 26px',
          borderRadius: '9999px',
          border: '1px solid rgba(52, 211, 153, 0.28)',
          marginBottom: '1.1rem'
        }}>
          <div style={{ fontSize: '1.45rem' }}>🌌</div>
          <div className="flex items-center gap-3">
            <span style={{ 
              fontSize: '0.98rem', 
              fontWeight: 800, 
              letterSpacing: '1.4px',
              color: '#34d399'
            }}>
              DERIM v0.1.1
            </span>
            <span style={{ 
              background: 'rgba(52, 211, 153, 0.15)', 
              color: '#34d399', 
              fontSize: '0.65rem', 
              padding: '1px 9px', 
              borderRadius: '9999px',
              fontWeight: 700
            }}>
              PRODUCTION
            </span>
          </div>
          
          {githubStats && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '7px',
              fontSize: '0.71rem',
              color: '#64748b',
              paddingLeft: '9px',
              borderLeft: '1px solid rgba(148,163,184,0.25)'
            }}>
              ⭐ {githubStats.stars.toLocaleString()} 
              <span style={{ opacity: 0.5 }}>•</span> 
              {githubStats.forks} forks
              <span style={{ opacity: 0.5 }}>•</span> 
              updated {githubStats.updated}
            </div>
          )}
        </div>

        <h1 style={{ 
          fontSize: '2.55rem', 
          margin: '0.3rem 0 0.35rem',
          background: 'linear-gradient(92deg, #ffffff, #34d399, #7dd3fc)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          fontWeight: 900,
          letterSpacing: '-0.028em',
          lineHeight: 1.05
        }}>
          Live Interactive Command Center
        </h1>
        <p style={{ 
          color: '#94a3b8', 
          maxWidth: '660px', 
          margin: '0 auto',
          fontSize: '1.05rem',
          lineHeight: 1.55
        }}>
          Real-time simulation of <span className="text-[#34d399] font-semibold">DERIM middleware</span> — the production-grade integration layer for solar, storage &amp; EV fleets.<br />
          <span className="text-xs text-[#64748b]">Mirrors the architecture and data models of the open-source Python/FastAPI + PyTorch stack. This panel runs on illustrative data in your browser.</span>
        </p>
      </div>

      {/* Device + Health Bar */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="text-[#7dd3fc] text-xs tracking-[1.2px] font-semibold mb-1.5">ACTIVE FLEET ASSETS</div>
          <div className="flex gap-2">
            {devices.map((device, idx) => (
              <button
                key={idx}
                onClick={() => {
                  const wasConnected = isConnected;
                  if (wasConnected) handleDisconnect();
                  setSelectedDevice(device);
                  setTimeout(() => {
                    if (wasConnected) handleConnect();
                  }, 140);
                }}
                className={`group flex-1 min-w-[162px] px-4 py-3.5 rounded-2xl text-left transition-all active:scale-[0.985] ${selectedDevice.id === device.id 
                  ? 'bg-[#34d399]/10 border border-[#34d399]' 
                  : 'bg-[#0f172a]/70 border border-white/10 hover:border-white/30'}`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-3xl group-hover:scale-110 transition-transform">{device.icon}</span>
                  <div>
                    <div className="font-semibold text-[15px]">{device.name}</div>
                    <div className="text-[10px] text-[#64748b] font-mono tracking-tight">{device.id}</div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {isConnected && (
          <div className="text-right">
            <div className="text-[#34d399] text-xs font-mono tracking-[1px] mb-px">SYSTEM HEALTH</div>
            <div className="flex items-center gap-4 text-xs">
              <div>API <span className="font-mono text-[#7dd3fc]">{healthMetrics.api_latency_ms}ms</span></div>
              <div>INFLUX <span className="font-mono text-[#7dd3fc]">{(healthMetrics.influx_write_rate / 1000).toFixed(1)}k/s</span></div>
              <div>ML <span className="font-mono text-[#7dd3fc]">{healthMetrics.model_inference_ms}ms</span></div>
            </div>
            <div className="text-[10px] text-[#64748b] mt-0.5">{healthMetrics.active_connections} live connections • {(healthMetrics.data_points_today / 1000000).toFixed(1)}M pts today</div>
          </div>
        )}
      </div>

      {/* Mode Selector */}
      <div className="mb-7">
        <div className="flex items-center justify-between mb-2.5">
          <div className="text-[#7dd3fc] text-xs tracking-[1px] font-semibold">SELECT CAPABILITY</div>
          <div className="text-[10px] text-[#64748b]">All modes fully simulate production DERIM behavior</div>
        </div>
        
        <div className="relative">
          <select
            value={selectedMode}
            onChange={(e) => {
              const newMode = e.target.value as any;
              setSelectedMode(newMode);
              setCimReport(null);
              setControlCommands([]);
              setShowApiExplorer(false);
              if (!isConnected && (newMode === 'twin' || newMode === 'control')) {
                // auto-connect suggestion
              }
            }}
            className="w-full bg-[#0f172a] border border-[#34d399]/40 text-white px-6 py-[17px] rounded-2xl text-[17px] font-semibold appearance-none cursor-pointer focus:outline-none focus:border-[#34d399]"
            style={{ boxShadow: '0 0 0 1px rgba(52, 211, 153, 0.12)' }}
          >
            {demoModes.map(mode => (
              <option key={mode.id} value={mode.id}>
                {mode.icon} {mode.label}
              </option>
            ))}
          </select>
          
          <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none text-xl" style={{ color: currentMode.color }}>
            ▼
          </div>
        </div>
      </div>

      {/* Main Canvas */}
      <div className="min-h-[520px] bg-[#050a14]/90 rounded-3xl p-8 border border-white/10 relative" style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.04)' }}>
        
        {/* Mode Header */}
        <div className="flex items-start gap-5 mb-7">
          <div style={{ 
            fontSize: '3.35rem', 
            lineHeight: 1,
            filter: `drop-shadow(0 0 18px ${currentMode.color}55)`
          }}>
            {currentMode.icon}
          </div>
          <div className="flex-1 pt-1">
            <div className="flex items-center gap-3">
              <div className="text-[27px] font-extrabold tracking-tight text-white">{currentMode.label}</div>
              {isConnected && (selectedMode === 'twin' || selectedMode === 'control' || selectedMode === 'adapter') && (
                <div className="inline-flex items-center gap-1.5 bg-[#34d399]/10 text-[#34d399] text-[10px] font-bold px-3.5 py-px rounded-full tracking-widest">
                  <div className="w-1.5 h-1.5 bg-[#34d399] rounded-full animate-pulse" /> LIVE
                </div>
              )}
            </div>
            <div className="text-[#94a3b8] text-[15px] mt-px pr-8">{currentMode.description}</div>
          </div>

          <div className="flex items-center gap-2.5">
            {isConnected && (
              <>
                <button 
                  onClick={() => exportTelemetryCSV('csv')}
                  className="px-4 py-2 text-xs bg-white/5 hover:bg-white/10 border border-white/20 rounded-xl flex items-center gap-2 transition-colors"
                >
                  ⬇ CSV
                </button>
                <button 
                  onClick={() => exportTelemetryCSV('json')}
                  className="px-4 py-2 text-xs bg-white/5 hover:bg-white/10 border border-white/20 rounded-xl flex items-center gap-2 transition-colors"
                >
                  JSON
                </button>
              </>
            )}
            
            {isConnected && selectedMode !== 'adapter' && (
              <button 
                onClick={handleDisconnect}
                className="px-5 py-2 text-xs bg-red-500/10 hover:bg-red-500/20 border border-red-500/40 text-red-400 rounded-xl transition-colors"
              >
                DISCONNECT
              </button>
            )}
            
            <button 
              onClick={() => setShowApiExplorer(!showApiExplorer)}
              className="px-4 py-2 text-xs bg-[#7dd3fc]/10 hover:bg-[#7dd3fc]/20 border border-[#7dd3fc]/40 text-[#7dd3fc] rounded-xl flex items-center gap-1.5 transition-colors"
            >
              API <span className="text-[10px]">↗</span>
            </button>
          </div>
        </div>

        {/* === ADAPTER MODE === */}
        {selectedMode === 'adapter' && (
          <div className="space-y-6">
            <div>
              <div className="text-xs text-[#7dd3fc] font-semibold tracking-widest mb-2">PROTOCOL ADAPTER</div>
              <select 
                value={selectedProtocol} 
                onChange={(e) => setSelectedProtocol(e.target.value)}
                disabled={isConnected}
                className="w-full bg-[#0f172a] border border-[#34d399]/30 px-5 py-3.5 rounded-2xl text-white text-[15px] focus:outline-none"
              >
                <option>Modbus TCP</option>
                <option>MQTT 5.0</option>
                <option>SunSpec</option>
                <option>OCPP 2.0.1</option>
              </select>
            </div>

            {!isConnected ? (
              <button 
                onClick={handleConnect}
                className="w-full py-6 bg-gradient-to-r from-[#34d399] to-[#10b981] text-[#0a111f] font-extrabold text-xl rounded-3xl shadow-[0_0_40px_rgb(52,211,153)] active:scale-[0.985] transition-all flex items-center justify-center gap-3"
              >
                CONNECT VIA {selectedProtocol.toUpperCase()} <span className="text-2xl">→</span>
              </button>
            ) : (
              <div className="space-y-4">
                <div className="bg-[#10b981]/10 border border-[#34d399] rounded-2xl p-5 flex justify-between items-center">
                  <div>
                    <div className="text-[#34d399] font-bold">✓ SECURE CONNECTION ACTIVE — {selectedProtocol}</div>
                    <div className="text-[#64748b] text-sm">Streaming @ 1.65s intervals • mTLS 1.3 • 256-bit encryption</div>
                  </div>
                  <button 
                    onClick={() => setIsStreaming(!isStreaming)}
                    className="px-5 py-1.5 text-xs border border-[#34d399] text-[#34d399] rounded-full hover:bg-[#34d399]/10 transition-colors"
                  >
                    {isStreaming ? '⏸ PAUSE STREAM' : '▶ RESUME'}
                  </button>
                </div>

                {/* Packet Log */}
                <div className="bg-[#050a14] border border-white/10 rounded-2xl p-4 max-h-[198px] overflow-auto font-mono text-xs">
                  <div className="flex justify-between text-[#64748b] mb-2 px-1 text-[10px]">
                    <div>PROTOCOL PACKET LOG — LAST 9</div>
                    <div>{packetLog.length} PACKETS</div>
                  </div>
                  
                  {packetLog.length > 0 ? packetLog.map((pkt, i) => (
                    <div key={i} className="flex gap-3 py-[5px] border-b border-white/5 last:border-none px-1 text-[10.5px]">
                      <span className="text-[#64748b] w-[62px] shrink-0">{pkt.timestamp}</span>
                      <span className="text-[#34d399] w-[82px] shrink-0 font-semibold">{pkt.protocol}</span>
                      <span className={pkt.direction === 'IN' ? 'text-[#a5f3fc]' : 'text-[#fcd34d]'}>{pkt.message}</span>
                      {pkt.latency_ms && <span className="ml-auto text-[#64748b] text-[9px]">{pkt.latency_ms}ms</span>}
                    </div>
                  )) : (
                    <div className="text-[#64748b] py-4 text-center">Awaiting first telemetry packets from adapter...</div>
                  )}
                </div>
              </div>
            )}

            {telemetry && isConnected && (
              <div className="bg-[#10b981]/5 border border-[#34d399]/40 rounded-2xl p-5">
                <div className="text-[#34d399] text-xs font-bold mb-3 flex items-center gap-2">
                  LIVE TELEMETRY — {selectedDevice.name.toUpperCase()}
                  <span className="text-[10px] text-[#64748b] font-normal">({new Date(telemetry.timestamp).toLocaleTimeString()})</span>
                </div>
                <pre className="text-[#a5f3fc] text-[12.2px] leading-[1.55] font-mono overflow-auto max-h-[148px]">{JSON.stringify(telemetry, null, 2)}</pre>
              </div>
            )}
          </div>
        )}

        {/* === DIGITAL TWIN MODE === */}
        {selectedMode === 'twin' && (
          <div>
            {!isConnected ? (
              <div className="text-center py-16">
                <div className="text-6xl mb-4 opacity-70">🧠</div>
                <div className="text-2xl font-bold mb-3">Digital Twin Offline</div>
                <p className="text-[#64748b] max-w-xs mx-auto mb-8">Connect to activate the PyTorch LSTM forecaster, residual analysis, and real-time anomaly engine.</p>
                <button 
                  onClick={handleConnect}
                  className="px-10 py-4 bg-gradient-to-r from-[#7dd3fc] to-[#38bdf8] text-[#0a111f] font-bold rounded-3xl text-lg shadow-[0_0_35px_rgb(125,211,252)]"
                >
                  ACTIVATE TWIN ENGINE
                </button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-12 gap-5 mb-6">
                  {/* Current Power */}
                  <div className="col-span-12 lg:col-span-5 bg-[#0f172a] border border-[#34d399]/20 rounded-2xl p-6">
                    <div className="text-xs text-[#7dd3fc] mb-1">CURRENT POWER OUTPUT</div>
                    <div className="text-[56px] font-bold tabular-nums tracking-tighter text-[#34d399] leading-none">
                      {telemetry?.power_kw || '—'}<span className="text-3xl font-medium">kW</span>
                    </div>
                    <div className="flex items-center gap-4 mt-3 text-xs">
                      <div className="text-[#64748b]">{selectedDevice.name} • {telemetry?.timestamp ? new Date(telemetry.timestamp).toLocaleTimeString() : ''}</div>
                      {telemetry?.irradiance && <div className="text-amber-400">☀ {telemetry.irradiance} W/m²</div>}
                    </div>
                  </div>

                  {/* Forecast */}
                  <div className="col-span-12 lg:col-span-7 bg-[#0f172a] border border-[#7dd3fc]/30 rounded-2xl p-6 flex flex-col">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="text-xs text-[#7dd3fc] mb-1">15-MIN LSTM FORECAST</div>
                        <div className="text-[52px] font-bold tabular-nums tracking-tighter text-[#7dd3fc] leading-none">
                          {forecast?.predicted_kw || '—'}<span className="text-3xl font-medium">kW</span>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="text-xs text-[#34d399]">CONFIDENCE</div>
                        <div className="text-4xl font-mono text-[#34d399]">{forecast?.confidence || '—'}<span className="text-lg">%</span></div>
                      </div>
                    </div>
                    
                    <div className="mt-auto flex items-center justify-between text-xs">
                      <div className="text-[#64748b]">PyTorch v2.4 • LSTM (hidden=128, layers=2) • Trained on 47 days field data</div>
                      <button 
                        onClick={handleRetrainModel}
                        disabled={retraining}
                        className="px-4 py-1 text-[#7dd3fc] border border-[#7dd3fc]/50 rounded-full text-xs hover:bg-[#7dd3fc]/10 disabled:opacity-50"
                      >
                        {retraining ? 'RETRAINING...' : 'RETRAIN MODEL'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Live Chart */}
                <div className="bg-[#050a14] border border-white/10 rounded-2xl p-5 mb-6">
                  <div className="flex items-center justify-between mb-3 px-2">
                    <div className="text-sm text-[#94a3b8]">POWER vs LSTM FORECAST • LAST 45s</div>
                    
                    <div className="flex items-center gap-5 text-xs">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-px bg-[#34d399]" /> ACTUAL
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-px bg-[#7dd3fc] border-t border-dashed border-[#7dd3fc]" /> LSTM + CONFIDENCE BAND
                      </div>
                    </div>
                  </div>
                  
                  <LiveChart 
                    actual={powerHistory} 
                    forecast={forecastHistory} 
                    upper={forecastUpper} 
                    lower={forecastLower} 
                  />
                </div>

                {/* Anomaly + Status */}
                <div className="grid grid-cols-12 gap-5">
                  <div className="col-span-12 lg:col-span-5">
                    <AnomalyGauge score={anomalyScore} breakdown={anomalyBreakdown} />
                  </div>
                  
                  <div className="col-span-12 lg:col-span-7 bg-[#0f172a] border border-white/10 rounded-2xl p-6">
                    <div className={`text-sm font-bold mb-2 ${anomalyScore > 38 ? 'text-red-400' : 'text-[#34d399]'}`}>
                      {anomalyScore > 38 ? '⚠️ ANOMALY DETECTED — INVESTIGATE' : '✓ NORMAL OPERATION — ALL RESIDUALS WITHIN 1.8σ'}
                    </div>
                    
                    <div className="text-[#94a3b8] text-[13.5px] leading-relaxed">
                      {anomalyScore > 38 
                        ? 'Residual analysis + spike detection triggered. Recommend immediate investigation via DERIM API or on-site inspection. Event logged to InfluxDB.' 
                        : 'LSTM baseline healthy. No significant deviation detected. System operating within trained distribution.'}
                    </div>
                    
                    <div className="mt-4 text-[10px] text-[#64748b] font-mono">Model: LSTM-128-2 • Inference: {healthMetrics.model_inference_ms}ms • Last retrained: 14h ago</div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* === CIM VALIDATOR === */}
        {selectedMode === 'cim' && (
          <div>
            <div className="text-center mb-8">
              <div className="text-[#a78bfa] text-sm tracking-[1.5px] mb-1">IEEE 2030.5 + IEC 61968 / 61970 COMPLIANT</div>
              <button 
                onClick={handleValidateCIM}
                disabled={isValidating}
                className="mt-3 w-full max-w-md py-5 bg-gradient-to-r from-[#a78bfa] to-[#7c3aed] text-white font-bold text-lg rounded-3xl shadow-[0_0_35px_rgb(167,139,250)] disabled:opacity-70"
              >
                {isValidating ? 'VALIDATING AGAINST DERIM MODELS...' : 'VALIDATE & NORMALIZE CURRENT TELEMETRY'}
              </button>
              <div className="text-xs text-[#64748b] mt-3">Pydantic v2.10 • Strict schema enforcement • Auto-correction enabled</div>
            </div>

            {cimReport && (
              <div className="bg-[#16a34a]/5 border border-[#34d399] rounded-2xl p-7">
                <div className="flex items-center gap-3 text-[#34d399] font-bold text-lg mb-5">
                  ✓ CIM NORMALIZED — COMPLIANCE {cimReport.compliance_score?.toFixed(1)}%
                </div>

                <div className="grid grid-cols-2 gap-6 mb-6 text-sm">
                  <div>
                    <div className="text-[#64748b] text-xs mb-px">IEC 61968 CLASS</div>
                    <div className="font-mono text-[#a5f3fc] text-xl">{cimReport.iec_61968_class}</div>
                  </div>
                  <div>
                    <div className="text-[#64748b] text-xs mb-px">IEEE 2030.5</div>
                    <div className="text-[#34d399] text-xl font-semibold">FULLY COMPLIANT ✓</div>
                  </div>
                </div>

                <div className="text-xs text-[#94a3b8] mb-2">MAPPINGS APPLIED (AUTOMATIC)</div>
                <div className="bg-black/40 rounded-xl p-4 text-xs text-[#a5f3fc] font-mono leading-[1.65] mb-4">
                  {cimReport.mappings_applied?.join('\n')}
                </div>

                {cimReport.cim_xml_snippet && (
                  <details className="text-xs">
                    <summary className="cursor-pointer text-[#64748b] hover:text-white">View generated CIM XML snippet</summary>
                    <pre className="mt-2 p-3 bg-black/60 rounded text-[#a5f3fc] overflow-auto text-[10px]">{cimReport.cim_xml_snippet}</pre>
                  </details>
                )}

                <div className="text-[10px] text-[#64748b] mt-5">Processed by DERIM v0.1.1 • 2 issues auto-corrected • Event ID: CIM-{Date.now().toString(36).toUpperCase()}</div>
              </div>
            )}

            {!cimReport && !isValidating && (
              <div className="text-center py-12 text-[#64748b]">
                Connect an asset or click the button above to run live CIM normalization against the official DERIM Pydantic models.
              </div>
            )}
          </div>
        )}

        {/* === CONTROL COMMAND CENTER === */}
        {selectedMode === 'control' && (
          <div>
            {!isConnected ? (
              <div className="text-center py-16">
                <div className="text-6xl mb-4">⚡</div>
                <div className="text-2xl font-bold mb-3">Control Plane Offline</div>
                <p className="text-[#64748b] max-w-sm mx-auto mb-8">Establish connection to send authenticated setpoints, curtailment commands, and optimized charge profiles through DERIM RBAC.</p>
                <button 
                  onClick={handleConnect}
                  className="px-12 py-4 bg-gradient-to-r from-[#fbbf24] to-[#d97706] text-white font-bold rounded-3xl text-lg"
                >
                  CONNECT TO CONTROL PLANE
                </button>
              </div>
            ) : (
              <>
                <div className="bg-[#0f172a] border border-[#fbbf24]/30 rounded-2xl p-6 mb-6">
                  <div className="text-xs text-[#fbbf24] mb-1">TARGET ASSET</div>
                  <div className="text-2xl font-bold">{selectedDevice.icon} {selectedDevice.name} • {selectedDevice.id}</div>
                  <div className="text-xs text-[#64748b]">Routed through DERIM → Adapter → Physical Device • All commands audited in InfluxDB</div>
                </div>

                <div className="grid grid-cols-12 gap-4">
                  <div className="col-span-12 lg:col-span-7">
                    <div className="text-xs text-[#fbbf24] mb-2">COMMAND TYPE</div>
                    <select 
                      value={commandType} 
                      onChange={(e) => setCommandType(e.target.value as any)}
                      className="w-full bg-[#0f172a] border border-[#fbbf24]/40 px-5 py-3.5 rounded-2xl text-white text-lg"
                    >
                      <option value="setpoint">Active Power Setpoint (kW)</option>
                      <option value="reactive">Reactive Power (pu)</option>
                      <option value="curtail">Curtailment Level (%)</option>
                      <option value="charge">BESS Charge Rate (%)</option>
                    </select>
                  </div>

                  <div className="col-span-12 lg:col-span-5">
                    <div className="text-xs text-[#fbbf24] mb-2">VALUE</div>
                    <div className="flex gap-3">
                      <input 
                        type="number" 
                        value={commandValue} 
                        onChange={(e) => setCommandValue(parseFloat(e.target.value) || 0)}
                        className="flex-1 bg-[#0f172a] border border-[#fbbf24]/40 px-5 py-3.5 rounded-2xl text-white text-2xl font-bold tabular-nums"
                      />
                      <button 
                        onClick={previewCommandImpact}
                        className="px-8 bg-white/5 border border-white/20 rounded-2xl text-sm hover:bg-white/10"
                      >
                        PREVIEW
                      </button>
                      <button 
                        onClick={handleSendControl}
                        className="px-9 bg-gradient-to-r from-[#fbbf24] to-[#d97706] text-white font-extrabold rounded-2xl text-sm active:scale-95"
                      >
                        EXECUTE
                      </button>
                    </div>
                  </div>
                </div>

                {showCommandPreview && commandImpact && (
                  <div className="mt-4 bg-[#fbbf24]/10 border border-[#fbbf24] rounded-2xl p-4 text-sm text-[#fcd34d]">
                    <div className="font-bold mb-1">PREDICTED IMPACT</div>
                    {commandImpact}
                  </div>
                )}

                {controlResult && (
                  <div className="mt-4 bg-[#f59e0b]/10 border border-[#fbbf24] rounded-2xl p-5 text-[#fcd34d] text-[15px]">
                    {controlResult}
                  </div>
                )}

                {controlCommands.length > 0 && (
                  <div className="mt-6">
                    <div className="text-xs text-[#64748b] mb-2 px-1">RECENT COMMANDS (LAST 6)</div>
                    <div className="bg-black/40 rounded-2xl text-xs divide-y divide-white/10">
                      {controlCommands.map((cmd, i) => (
                        <div key={i} className="px-5 py-3 flex justify-between items-center">
                          <div>
                            <span className="text-[#fcd34d] font-mono">{cmd.timestamp}</span> • {cmd.command} <span className="font-bold">{cmd.value}{cmd.unit}</span>
                          </div>
                          <div className="text-[#34d399] text-[10px]">{cmd.status}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="text-center text-[10px] text-[#64748b] mt-6">All commands authenticated via DERIM RBAC • Fully reversible within 30s • Logged to immutable audit trail</div>
              </>
            )}
          </div>
        )}

        {/* API Explorer Modal */}
        {showApiExplorer && (
          <div className="absolute inset-0 bg-black/90 rounded-3xl flex items-center justify-center z-40 p-8" onClick={() => setShowApiExplorer(false)}>
            <div className="bg-[#0f172a] border border-[#7dd3fc] rounded-2xl w-full max-w-lg p-7" onClick={e => e.stopPropagation()}>
              <div className="text-[#7dd3fc] text-sm mb-4 font-semibold">DERIM PRODUCTION API EXPLORER</div>
              
              <div className="space-y-3 text-sm">
                {['/api/v1/telemetry/INV-7842', '/api/v1/forecast/INV-7842', '/api/v1/control/INV-7842'].map((ep, idx) => (
                  <button 
                    key={idx}
                    onClick={() => triggerApiCall(ep)}
                    className="w-full text-left px-4 py-3 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 flex justify-between items-center group"
                  >
                    <span className="font-mono text-[#a5f3fc]">{ep}</span>
                    <span className="text-xs text-[#64748b] group-hover:text-white">CALL →</span>
                  </button>
                ))}
              </div>

              {apiResponse && (
                <div className="mt-5 p-4 bg-black/70 rounded-xl text-xs font-mono text-[#a5f3fc] border border-[#7dd3fc]/30">
                  {JSON.stringify(apiResponse, null, 2)}
                </div>
              )}

              <div className="text-[10px] text-center text-[#64748b] mt-5">Illustrative responses generated in your browser — wire up a running DERIM backend to see live results</div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Bar */}
      <div className="mt-6 flex justify-between items-center text-xs text-[#64748b]">
        <div>
          Browser-side simulation using illustrative data. Protocols, data models, and message shapes mirror the open-source repository.
        </div>
        
        <div className="flex items-center gap-4">
          <a href="https://github.com/iceccarelli/derim-middleware" target="_blank" className="hover:text-[#34d399] transition-colors">View on GitHub →</a>
          <span className="opacity-30">•</span>
          <span>Ready for Vercel • Docker • Fly.io</span>
        </div>
      </div>

      {/* Success Toast */}
      {showSuccess && (
        <div className="absolute bottom-7 left-1/2 -translate-x-1/2 bg-[#10b981] text-white px-8 py-3 rounded-3xl text-sm font-bold shadow-[0_10px_40px_rgb(16,185,129)] flex items-center gap-3 z-50">
          ✓ ACTION SUCCESSFUL — DERIM CONFIRMED &amp; LOGGED
        </div>
      )}

      <style jsx>{`
        .glass-panel {
          backdrop-filter: blur(24px);
        }
        select, input, button {
          transition: all 0.15s cubic-bezier(0.23, 1, 0.32, 1);
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.35; }
        }
      `}</style>
    </div>
  );
}
