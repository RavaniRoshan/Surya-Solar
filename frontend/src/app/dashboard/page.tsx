'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import {
  AlertTriangle,
  Zap,
  RefreshCw,
  ExternalLink,
  Activity,
  Wifi,
  Clock,
  Thermometer,
  BarChart3,
  TrendingUp
} from 'lucide-react'

export const dynamic = 'force-dynamic'

// Mock data for demo - would come from WebSocket in production
const mockEvents = [
  {
    id: 1,
    type: 'x-class',
    title: 'X-Class Flare Detected',
    description: 'Magnitude 1.2 from Active Region 3664. Probability of HF Radio Blackout: 85%.',
    time: '16:42:01 UTC',
    icon: AlertTriangle,
    color: 'red'
  },
  {
    id: 2,
    type: 'm-class',
    title: 'M-Class Activity Increase',
    description: 'Surya-1.0 forecasting 3 consecutive M-class events in next 12 hours.',
    time: '16:38:15 UTC',
    icon: Zap,
    color: 'amber'
  },
  {
    id: 3,
    type: 'sync',
    title: 'Satellite Data Sync Complete',
    description: 'GOES-16 Full Spectral Data synchronized with 99.9% integrity.',
    time: '16:15:00 UTC',
    icon: RefreshCw,
    color: 'cyan'
  }
]

// Generate chart data points
function generateChartData() {
  const points = []
  const now = new Date()
  for (let i = 0; i < 20; i++) {
    const time = new Date(now.getTime() - (20 - i) * 6 * 60 * 1000)
    points.push({
      time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      value: 30 + Math.sin(i * 0.5) * 20 + Math.random() * 15
    })
  }
  return points
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [chartData, setChartData] = useState(generateChartData())
  const [activeTab, setActiveTab] = useState('xray')

  useEffect(() => {
    const interval = setInterval(() => {
      setChartData(generateChartData())
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Live Solar Intensity Chart - Takes 8 columns */}
        <div className="col-span-12 lg:col-span-8">
          <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-white">Live Solar Intensity</h2>
                <p className="text-sm text-gray-500">Real-time spectral flux monitoring from Surya-1.0</p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setActiveTab('xray')}
                  className={`px-4 py-1.5 text-xs font-medium rounded-lg transition-colors ${activeTab === 'xray'
                      ? 'bg-cyan-600 text-white'
                      : 'bg-[#1a1a24] text-gray-400 hover:text-white'
                    }`}
                >
                  X-Ray Flux
                </button>
                <button
                  onClick={() => setActiveTab('proton')}
                  className={`px-4 py-1.5 text-xs font-medium rounded-lg transition-colors ${activeTab === 'proton'
                      ? 'bg-cyan-600 text-white'
                      : 'bg-[#1a1a24] text-gray-400 hover:text-white'
                    }`}
                >
                  Proton
                </button>
              </div>
            </div>

            {/* Chart Area */}
            <div className="relative h-64">
              {/* Grid lines */}
              <div className="absolute inset-0 flex flex-col justify-between">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="border-t border-[#1a1a24] w-full" />
                ))}
              </div>

              {/* Chart SVG */}
              <svg className="absolute inset-0 w-full h-full" viewBox="0 0 800 250" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
                  </linearGradient>
                </defs>

                {/* Area fill */}
                <path
                  d={`M 0 ${250 - chartData[0].value * 2} ${chartData.map((d, i) =>
                    `L ${i * (800 / (chartData.length - 1))} ${250 - d.value * 2}`
                  ).join(' ')} L 800 250 L 0 250 Z`}
                  fill="url(#chartGradient)"
                />

                {/* Line */}
                <path
                  d={`M 0 ${250 - chartData[0].value * 2} ${chartData.map((d, i) =>
                    `L ${i * (800 / (chartData.length - 1))} ${250 - d.value * 2}`
                  ).join(' ')}`}
                  fill="none"
                  stroke="#06b6d4"
                  strokeWidth="2"
                />
              </svg>

              {/* Time labels */}
              <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-gray-600 pt-2">
                <span>14:00</span>
                <span>14:30</span>
                <span>15:00</span>
                <span>15:30</span>
                <span>16:00</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sun Activity Map - Takes 4 columns */}
        <div className="col-span-12 lg:col-span-4">
          <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-6 h-full">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-white">Sun Activity Map</h3>
              <p className="text-xs text-gray-500">Region 3664 / 3665 Active</p>
            </div>

            {/* Sun visualization */}
            <div className="relative flex items-center justify-center py-4">
              <div className="relative w-36 h-36">
                {/* Sun glow */}
                <div className="absolute inset-0 bg-orange-500/20 rounded-full blur-xl" />
                <div className="absolute inset-2 bg-gradient-to-br from-orange-400 via-orange-500 to-orange-600 rounded-full shadow-lg shadow-orange-500/30">
                  {/* Sunspots */}
                  <div className="absolute top-8 left-10 w-3 h-3 bg-orange-800/50 rounded-full" />
                  <div className="absolute top-12 left-14 w-2 h-2 bg-orange-800/40 rounded-full" />
                  <div className="absolute bottom-10 right-8 w-4 h-4 bg-orange-800/50 rounded-full" />
                </div>
                {/* Activity ring */}
                <svg className="absolute inset-0 w-full h-full -rotate-90">
                  <circle
                    cx="72"
                    cy="72"
                    r="68"
                    fill="none"
                    stroke="#2a2a3a"
                    strokeWidth="2"
                    strokeDasharray="4 4"
                  />
                </svg>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="bg-[#1a1a24] rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500 uppercase mb-1">Surface Temp</div>
                <div className="text-xl font-bold text-white">5,778 K</div>
              </div>
              <div className="bg-[#1a1a24] rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500 uppercase mb-1">Spots Count</div>
                <div className="text-xl font-bold text-white">124</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-12 gap-6">
        {/* Real-Time Event Log - Takes 8 columns */}
        <div className="col-span-12 lg:col-span-8">
          <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white">Real-Time Event Log</h3>
              <div className="flex items-center space-x-2 text-xs text-cyan-400">
                <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span>Streaming Live Data</span>
              </div>
            </div>

            <div className="space-y-4">
              {mockEvents.map((event) => {
                const Icon = event.icon
                const colors: Record<string, string> = {
                  red: 'bg-red-500/20 text-red-400 border-red-500/30',
                  amber: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
                  cyan: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
                }

                return (
                  <div
                    key={event.id}
                    className="flex items-start space-x-4 p-4 bg-[#1a1a24] rounded-xl border border-[#2a2a3a] hover:border-purple-500/30 transition-colors"
                  >
                    <div className={`p-2 rounded-lg ${colors[event.color]} border`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-white">{event.title}</h4>
                        <span className="text-xs text-gray-500">{event.time}</span>
                      </div>
                      <p className="text-sm text-gray-400 mt-1">{event.description}</p>
                    </div>
                    <button className="p-1 text-gray-500 hover:text-white transition-colors">
                      <ExternalLink className="w-4 h-4" />
                    </button>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Stats Cards - Takes 4 columns */}
        <div className="col-span-12 lg:col-span-4 space-y-4">
          {/* API Requests */}
          <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <Activity className="w-4 h-4 text-purple-400" />
                  <span className="text-xs text-gray-500 uppercase">API Requests (24H)</span>
                </div>
                <div className="text-3xl font-bold text-white">1.2M</div>
              </div>
              <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">
                +12% vs avg
              </span>
            </div>
          </div>

          {/* Latency */}
          <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <Clock className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs text-gray-500 uppercase">Current Latency (MS)</span>
                </div>
                <div className="text-3xl font-bold text-white">42.8 ms</div>
              </div>
              <span className="text-xs text-emerald-400">Stable</span>
            </div>
          </div>

          {/* Active Webhooks */}
          <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <Wifi className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs text-gray-500 uppercase">Active Webhooks</span>
                </div>
                <div className="text-3xl font-bold text-white">8,412</div>
              </div>
              <span className="text-xs text-cyan-400 flex items-center space-x-1">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                <span>Live</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-4 flex items-center space-x-4">
          <div className="w-1 h-10 bg-purple-500 rounded-full" />
          <div>
            <div className="text-xs text-gray-500 uppercase">Prediction Confidence</div>
            <div className="text-xl font-bold text-white font-mono">94.2%</div>
          </div>
        </div>

        <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-4 flex items-center space-x-4">
          <div className="w-1 h-10 bg-cyan-500 rounded-full" />
          <div>
            <div className="text-xs text-gray-500 uppercase">Solar Wind Speed</div>
            <div className="text-xl font-bold text-white font-mono">450 km/s</div>
          </div>
        </div>

        <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-4 flex items-center space-x-4">
          <div className="w-1 h-10 bg-amber-500 rounded-full" />
          <div>
            <div className="text-xs text-gray-500 uppercase">Magnetic Fields</div>
            <div className="text-xl font-bold text-white font-mono">5.4 nT</div>
          </div>
        </div>

        <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-4 flex items-center space-x-4">
          <div className="w-1 h-10 bg-emerald-500 rounded-full" />
          <div>
            <div className="text-xs text-gray-500 uppercase">Uptime (30D)</div>
            <div className="text-xl font-bold text-white font-mono">99.998%</div>
          </div>
        </div>
      </div>
    </div>
  )
}