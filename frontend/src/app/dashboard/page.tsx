'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowUp, Satellite, Clock, BarChart3, Globe, ArrowRight } from 'lucide-react'

export const dynamic = 'force-dynamic'

// Mock live alert data
const mockAlerts = [
  {
    id: 1,
    severity: 'HIGH SEVERITY',
    severityColor: 'text-red-500',
    bgColor: 'bg-red-500/10 border-l-red-500',
    title: 'X-Class Flare Detected',
    description: 'Satellite orbital correction advised in Sector 7-6.',
    time: '14:22 UTC'
  },
  {
    id: 2,
    severity: 'MEDIUM SEVERITY',
    severityColor: 'text-orange-500',
    bgColor: 'bg-orange-500/10 border-l-orange-500',
    title: 'M-Class Prob. Increase',
    description: 'Sustained ionospheric disturbance detected.',
    time: '13:45 UTC'
  },
  {
    id: 3,
    severity: 'LOW SEVERITY',
    severityColor: 'text-green-500',
    bgColor: 'bg-green-500/10 border-l-green-500',
    title: 'Routine Status Update',
    description: 'Solar radiation levels normalized.',
    time: '13:18 UTC'
  }
]

// Generate chart data points for the solar flare probability curve
function generateChartPoints() {
  return [
    { x: 0, y: 60 },
    { x: 50, y: 55 },
    { x: 100, y: 45 },
    { x: 150, y: 50 },
    { x: 200, y: 55 },
    { x: 250, y: 48 },
    { x: 300, y: 52 },
    { x: 350, y: 58 },
    { x: 400, y: 70 },
    { x: 450, y: 85 },
    { x: 500, y: 75 },
    { x: 550, y: 65 },
  ]
}

export default function DashboardPage() {
  const [chartMode, setChartMode] = useState<'hourly' | 'live'>('live')
  const chartPoints = generateChartPoints()

  // Create SVG path from points
  const pathD = chartPoints.map((p, i) =>
    `${i === 0 ? 'M' : 'L'} ${p.x} ${150 - p.y}`
  ).join(' ')

  const areaD = pathD + ` L ${chartPoints[chartPoints.length - 1].x} 150 L 0 150 Z`

  return (
    <div className="space-y-6">
      {/* Main Grid - Chart and Live Alerts */}
      <div className="grid grid-cols-12 gap-6">
        {/* Solar Flare Probability Chart */}
        <div className="col-span-12 lg:col-span-8">
          <div className="bg-gray-900/50 border border-gray-800/50 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold text-white">Solar Flare Probability</h2>
                <p className="text-sm text-gray-500">Real-time predictive analysis (24h window)</p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setChartMode('hourly')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${chartMode === 'hourly'
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-400 hover:text-white'
                    }`}
                >
                  HOURLY
                </button>
                <button
                  onClick={() => setChartMode('live')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${chartMode === 'live'
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-400 hover:text-white'
                    }`}
                >
                  LIVE
                </button>
              </div>
            </div>

            {/* Chart */}
            <div className="relative h-64">
              <svg className="w-full h-full" viewBox="0 0 550 150" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#f97316" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#f97316" stopOpacity="0" />
                  </linearGradient>
                </defs>

                {/* Grid lines */}
                {[0, 37, 75, 112, 150].map((y) => (
                  <line key={y} x1="0" y1={y} x2="550" y2={y} stroke="#1f2937" strokeWidth="1" />
                ))}

                {/* Area fill */}
                <motion.path
                  d={areaD}
                  fill="url(#chartGradient)"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 1 }}
                />

                {/* Line */}
                <motion.path
                  d={pathD}
                  fill="none"
                  stroke="#f97316"
                  strokeWidth="3"
                  strokeLinecap="round"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 2, ease: "easeOut" }}
                />
              </svg>

              {/* Time labels */}
              <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-gray-600 pt-2">
                <span>00:00</span>
                <span>04:00</span>
                <span>08:00</span>
                <span>12:00</span>
                <span>16:00</span>
                <span>20:00</span>
              </div>
            </div>
          </div>
        </div>

        {/* Live Alert Feed */}
        <div className="col-span-12 lg:col-span-4">
          <div className="bg-gray-900/50 border border-gray-800/50 rounded-2xl p-6 h-full">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-white">Live Alert Feed</h2>
              <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 text-xs font-medium rounded-full">
                Active
              </span>
            </div>

            <div className="space-y-4">
              {mockAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-4 rounded-xl border-l-4 ${alert.bgColor} border border-gray-800/50`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-bold uppercase ${alert.severityColor}`}>
                      {alert.severity}
                    </span>
                    <span className="text-xs text-gray-500">{alert.time}</span>
                  </div>
                  <h3 className="font-semibold text-white text-sm">{alert.title}</h3>
                  <p className="text-xs text-gray-400 mt-1">{alert.description}</p>
                </div>
              ))}
            </div>

            <button className="w-full mt-4 py-3 text-center text-sm text-gray-400 hover:text-white transition-colors uppercase tracking-wider font-medium">
              VIEW ALERT HISTORY
            </button>
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-12 gap-6">
        {/* Active Satellites */}
        <div className="col-span-6 lg:col-span-3">
          <div className="bg-gray-900/50 border border-gray-800/50 rounded-2xl p-6">
            <div className="flex items-center space-x-3 mb-2">
              <Satellite className="w-5 h-5 text-blue-400" />
              <span className="text-xs text-gray-500 uppercase tracking-wider">ACTIVE SATELLITES</span>
            </div>
            <div className="text-4xl font-bold text-white font-mono">14,802</div>
            <div className="flex items-center space-x-1 mt-2 text-emerald-400 text-sm">
              <ArrowUp className="w-4 h-4" />
              <span>+0.4% from avg</span>
            </div>
          </div>
        </div>

        {/* Next Predicted Event */}
        <div className="col-span-6 lg:col-span-3">
          <div className="bg-gray-900/50 border border-gray-800/50 rounded-2xl p-6">
            <div className="flex items-center space-x-3 mb-2">
              <Clock className="w-5 h-5 text-orange-400" />
              <span className="text-xs text-gray-500 uppercase tracking-wider">NEXT PREDICTED EVENT</span>
            </div>
            <div className="text-4xl font-bold text-white font-mono">03h 42m</div>
            <div className="text-sm text-gray-500 mt-2">EST. M-CLASS FLARE</div>
          </div>
        </div>

        {/* Avg Flare Severity */}
        <div className="col-span-6 lg:col-span-3">
          <div className="bg-gray-900/50 border border-gray-800/50 rounded-2xl p-6">
            <div className="flex items-center space-x-3 mb-2">
              <BarChart3 className="w-5 h-5 text-purple-400" />
              <span className="text-xs text-gray-500 uppercase tracking-wider">AVG FLARE SEVERITY</span>
            </div>
            <div className="text-4xl font-bold text-white font-serif italic">Level 2.4</div>
            <div className="text-sm text-gray-500 mt-2">Moderate Risk Index</div>
          </div>
        </div>

        {/* Impact Zones */}
        <div className="col-span-6 lg:col-span-3">
          <div className="bg-gray-900/50 border border-gray-800/50 rounded-2xl p-6">
            <div className="flex items-center space-x-3 mb-2">
              <Globe className="w-5 h-5 text-cyan-400" />
              <span className="text-xs text-gray-500 uppercase tracking-wider">IMPACT ZONES</span>
            </div>
            {/* Mini world map placeholder */}
            <div className="h-12 bg-gray-800/50 rounded-lg mb-2 flex items-center justify-center">
              <div className="w-20 h-10 bg-gradient-to-r from-cyan-900/50 to-blue-900/50 rounded" />
            </div>
            <p className="text-xs text-gray-400">North Atlantic Corridor currently experiencing high radiation flux.</p>
            <Link href="/dashboard/impact" className="flex items-center text-orange-400 text-xs font-medium mt-2 hover:text-orange-300 transition-colors">
              OPEN GLOBAL VIEW <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}