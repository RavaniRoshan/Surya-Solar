'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Calendar, Download } from 'lucide-react'
import { AlertData, HistoricalAlertsResponse } from '@/types/dashboard'
import { api } from '@/lib/api-client'
import { useWebSocket } from '@/hooks/useWebSocket'

interface HistoricalChartProps {
  className?: string
}

interface ChartDataPoint {
  timestamp: string
  probability: number
  severity: string
  formattedTime: string
}

const severityColors = {
  low: '#10b981',
  medium: '#f59e0b', 
  high: '#ef4444'
}

export default function HistoricalChart({ className = '' }: HistoricalChartProps) {
  const [chartData, setChartData] = useState<ChartDataPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h')

  // Listen for real-time updates to add new data points
  useWebSocket({
    onMessage: (message) => {
      if (message.type === 'alert' && message.data && timeRange === '24h') {
        const alertData = message.data
        const newDataPoint: ChartDataPoint = {
          timestamp: alertData.last_updated,
          probability: alertData.current_probability * 100,
          severity: alertData.severity_level,
          formattedTime: new Date(alertData.last_updated).toLocaleString()
        }
        
        setChartData(prevData => {
          // Add new point and keep only last 24 hours for real-time view
          const cutoffTime = new Date(Date.now() - 24 * 60 * 60 * 1000)
          const filteredData = prevData.filter(point => 
            new Date(point.timestamp) > cutoffTime
          )
          
          // Add new point and sort by timestamp
          const updatedData = [...filteredData, newDataPoint]
            .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
          
          return updatedData
        })
      }
    }
  })

  const fetchHistoricalData = async () => {
    try {
      setLoading(true)
      
      const endTime = new Date()
      const startTime = new Date()
      
      switch (timeRange) {
        case '24h':
          startTime.setHours(startTime.getHours() - 24)
          break
        case '7d':
          startTime.setDate(startTime.getDate() - 7)
          break
        case '30d':
          startTime.setDate(startTime.getDate() - 30)
          break
      }

      const response = await api.alerts.getHistory({
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        limit: 1000
      })

      const data: HistoricalAlertsResponse = response.data
      
      const formattedData: ChartDataPoint[] = data.alerts.map((alert: AlertData) => ({
        timestamp: alert.timestamp,
        probability: alert.flare_probability * 100, // Convert to percentage
        severity: alert.severity_level,
        formattedTime: new Date(alert.timestamp).toLocaleString()
      })).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())

      setChartData(formattedData)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch historical data:', err)
      setError('Failed to load historical data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistoricalData()
  }, [timeRange]) // eslint-disable-line react-hooks/exhaustive-deps

  const exportData = () => {
    const csvContent = [
      ['Timestamp', 'Probability (%)', 'Severity Level'],
      ...chartData.map(point => [
        point.timestamp,
        point.probability.toString(),
        point.severity
      ])
    ].map(row => row.join(',')).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `solar-weather-data-${timeRange}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: ChartDataPoint }> }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm text-gray-600">{data.formattedTime}</p>
          <p className="text-sm font-semibold">
            Probability: <span className="text-blue-600">{data.probability.toFixed(1)}%</span>
          </p>
          <p className="text-sm">
            Severity: <span className={`font-semibold capitalize`} style={{ color: severityColors[data.severity as keyof typeof severityColors] }}>
              {data.severity}
            </span>
          </p>
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="text-red-600 text-center">
          <Calendar className="h-8 w-8 mx-auto mb-2" />
          <p>{error}</p>
          <button 
            onClick={fetchHistoricalData}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 sm:mb-0">Historical Data</h2>
        
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="flex rounded-md shadow-sm">
            {(['24h', '7d', '30d'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-2 text-sm font-medium border ${
                  timeRange === range
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                } ${range === '24h' ? 'rounded-l-md' : range === '30d' ? 'rounded-r-md' : ''}`}
              >
                {range === '24h' ? '24 Hours' : range === '7d' ? '7 Days' : '30 Days'}
              </button>
            ))}
          </div>
          
          <button
            onClick={exportData}
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </button>
        </div>
      </div>

      {chartData.length === 0 ? (
        <div className="text-center text-gray-500 py-12">
          <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No historical data available for the selected time range</p>
        </div>
      ) : (
        <div className="h-64 sm:h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="timestamp"
                tickFormatter={(value) => {
                  const date = new Date(value)
                  return timeRange === '24h' 
                    ? date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    : date.toLocaleDateString([], { month: 'short', day: 'numeric' })
                }}
                stroke="#6b7280"
                fontSize={12}
              />
              <YAxis 
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
                stroke="#6b7280"
                fontSize={12}
              />
              <Tooltip content={<CustomTooltip />} />
              
              {/* Reference lines for severity thresholds */}
              <ReferenceLine y={25} stroke={severityColors.low} strokeDasharray="2 2" />
              <ReferenceLine y={50} stroke={severityColors.medium} strokeDasharray="2 2" />
              <ReferenceLine y={75} stroke={severityColors.high} strokeDasharray="2 2" />
              
              <Line 
                type="monotone" 
                dataKey="probability" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 3 }}
                activeDot={{ r: 5, stroke: '#3b82f6', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
        <div className="flex items-center">
          <div className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: severityColors.low }}></div>
          Low Risk (0-25%)
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: severityColors.medium }}></div>
          Medium Risk (25-50%)
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: severityColors.high }}></div>
          High Risk (50%+)
        </div>
      </div>
    </div>
  )
}