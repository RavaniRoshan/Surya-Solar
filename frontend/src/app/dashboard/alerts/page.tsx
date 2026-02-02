'use client'

import { useState } from 'react'
import {
    Plus,
    Link as LinkIcon,
    Mail,
    MessageSquare,
    Hash,
    Check
} from 'lucide-react'

// Mock data for existing alerts
const mockAlerts = [
    {
        id: 1,
        name: 'X-Class Flare Alert',
        location: 'Global Coverage',
        trigger: { type: 'intensity', operator: '>', value: 'X-1.0', color: 'red' },
        delivery: ['webhook', 'email'],
        enabled: true
    },
    {
        id: 2,
        name: 'High KP Index',
        location: 'Power Grid Node-04',
        trigger: { type: 'kp', operator: '>', value: '5.0', color: 'purple' },
        delivery: ['email', 'webhook'],
        enabled: true
    },
    {
        id: 3,
        name: 'Solar Wind Spike',
        location: 'Uplink Station B',
        trigger: { type: 'wind', operator: '>', value: '500 km/s', color: 'gray' },
        delivery: ['email'],
        enabled: false
    }
]

const deliveryChannels = [
    { id: 'email', name: 'EMAIL', icon: Mail },
    { id: 'webhook', name: 'WEBHOOK', icon: LinkIcon },
    { id: 'discord', name: 'DISCORD', icon: MessageSquare },
    { id: 'slack', name: 'SLACK', icon: Hash },
]

export default function AlertsPage() {
    const [alerts, setAlerts] = useState(mockAlerts)
    const [selectedChannels, setSelectedChannels] = useState(['webhook'])
    const [threshold, setThreshold] = useState(70) // 0-100, maps to C/M/X class
    const [alertName, setAlertName] = useState('')
    const [triggerSource, setTriggerSource] = useState('flare')
    const [condition, setCondition] = useState('greater')

    const toggleAlert = (id: number) => {
        setAlerts(prev => prev.map(alert =>
            alert.id === id ? { ...alert, enabled: !alert.enabled } : alert
        ))
    }

    const toggleChannel = (channelId: string) => {
        setSelectedChannels(prev =>
            prev.includes(channelId)
                ? prev.filter(c => c !== channelId)
                : [...prev, channelId]
        )
    }

    const getThresholdLabel = () => {
        if (threshold < 33) return { class: 'C-Class', value: `C-${(threshold / 33 * 10).toFixed(1)}` }
        if (threshold < 66) return { class: 'M-Class', value: `M-${((threshold - 33) / 33 * 10).toFixed(1)}` }
        return { class: 'X-Class', value: `X-${((threshold - 66) / 34 * 10).toFixed(1)}` }
    }

    const thresholdInfo = getThresholdLabel()

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Alert Configurations</h1>
                    <p className="text-gray-500 mt-1">
                        Manage and monitor automated triggers for solar events across your infrastructure.
                    </p>
                </div>
                <button className="px-4 py-2 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 rounded-lg font-medium text-white flex items-center space-x-2 transition-all">
                    <Plus className="w-4 h-4" />
                    <span>Create New Alert</span>
                </button>
            </div>

            <div className="grid grid-cols-12 gap-6">
                {/* Active Notifications Table */}
                <div className="col-span-12 lg:col-span-7">
                    <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl">
                        <div className="p-4 border-b border-[#2a2a3a]">
                            <h2 className="text-lg font-semibold text-white">Active Notifications</h2>
                        </div>

                        {/* Table Header */}
                        <div className="grid grid-cols-12 gap-4 px-4 py-3 text-xs text-gray-500 uppercase tracking-wider border-b border-[#2a2a3a]">
                            <div className="col-span-4">Alert Name</div>
                            <div className="col-span-3">Trigger</div>
                            <div className="col-span-3">Delivery</div>
                            <div className="col-span-2 text-right">Status</div>
                        </div>

                        {/* Table Body */}
                        <div className="divide-y divide-[#2a2a3a]">
                            {alerts.map((alert) => (
                                <div key={alert.id} className="grid grid-cols-12 gap-4 px-4 py-4 items-center hover:bg-[#1a1a24] transition-colors">
                                    <div className="col-span-4">
                                        <div className="font-medium text-white">{alert.name}</div>
                                        <div className="text-xs text-gray-500">{alert.location}</div>
                                    </div>
                                    <div className="col-span-3">
                                        <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-mono ${alert.trigger.color === 'red' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                                                alert.trigger.color === 'purple' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' :
                                                    'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                                            }`}>
                                            {alert.trigger.type === 'intensity' ? 'Intensity' : alert.trigger.type === 'kp' ? 'KP' : ''} {alert.trigger.operator} {alert.trigger.value}
                                        </span>
                                    </div>
                                    <div className="col-span-3">
                                        <div className="flex items-center space-x-2">
                                            {alert.delivery.includes('webhook') && (
                                                <LinkIcon className="w-4 h-4 text-gray-400" />
                                            )}
                                            {alert.delivery.includes('email') && (
                                                <Mail className="w-4 h-4 text-gray-400" />
                                            )}
                                        </div>
                                    </div>
                                    <div className="col-span-2 flex justify-end">
                                        <button
                                            onClick={() => toggleAlert(alert.id)}
                                            className={`relative w-12 h-6 rounded-full transition-colors ${alert.enabled ? 'bg-purple-600' : 'bg-[#2a2a3a]'
                                                }`}
                                        >
                                            <span className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${alert.enabled ? 'left-7' : 'left-1'
                                                }`} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Configure Trigger Panel */}
                <div className="col-span-12 lg:col-span-5">
                    <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-6">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="p-2 bg-purple-600/20 rounded-lg">
                                <Hash className="w-5 h-5 text-purple-400" />
                            </div>
                            <h2 className="text-lg font-semibold text-white">Configure Trigger</h2>
                        </div>

                        <div className="space-y-5">
                            {/* Alert Name */}
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Alert Name</label>
                                <input
                                    type="text"
                                    value={alertName}
                                    onChange={(e) => setAlertName(e.target.value)}
                                    placeholder="e.g., Satellite Comms Redline"
                                    className="w-full px-4 py-3 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-600 focus:border-purple-500 focus:outline-none transition-colors"
                                />
                            </div>

                            {/* Trigger Source & Condition */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">Trigger Source</label>
                                    <select
                                        value={triggerSource}
                                        onChange={(e) => setTriggerSource(e.target.value)}
                                        className="w-full px-4 py-3 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white focus:border-purple-500 focus:outline-none transition-colors appearance-none"
                                    >
                                        <option value="flare">Flare Intensity</option>
                                        <option value="kp">KP Index</option>
                                        <option value="wind">Solar Wind</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">Condition</label>
                                    <select
                                        value={condition}
                                        onChange={(e) => setCondition(e.target.value)}
                                        className="w-full px-4 py-3 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white focus:border-purple-500 focus:outline-none transition-colors appearance-none"
                                    >
                                        <option value="greater">Greater than</option>
                                        <option value="less">Less than</option>
                                        <option value="equals">Equals</option>
                                    </select>
                                </div>
                            </div>

                            {/* Intensity Threshold */}
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <label className="text-sm text-gray-400">Intensity Threshold</label>
                                    <span className="text-sm text-red-400 font-medium">
                                        {thresholdInfo.class} ({thresholdInfo.value})
                                    </span>
                                </div>
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={threshold}
                                    onChange={(e) => setThreshold(Number(e.target.value))}
                                    className="w-full h-2 bg-[#2a2a3a] rounded-lg appearance-none cursor-pointer accent-purple-500"
                                />
                                <div className="flex justify-between text-xs text-gray-600 mt-1">
                                    <span>C-CLASS</span>
                                    <span>M-CLASS</span>
                                    <span>X-CLASS</span>
                                </div>
                            </div>

                            {/* Delivery Channels */}
                            <div>
                                <label className="block text-sm text-gray-400 mb-3">Delivery Channels</label>
                                <div className="grid grid-cols-4 gap-2">
                                    {deliveryChannels.map((channel) => {
                                        const Icon = channel.icon
                                        const isSelected = selectedChannels.includes(channel.id)
                                        return (
                                            <button
                                                key={channel.id}
                                                onClick={() => toggleChannel(channel.id)}
                                                className={`p-3 rounded-lg border text-center transition-all ${isSelected
                                                        ? 'bg-purple-600/20 border-purple-500/50 text-purple-400'
                                                        : 'bg-[#1a1a24] border-[#2a2a3a] text-gray-500 hover:border-gray-600'
                                                    }`}
                                            >
                                                <Icon className="w-5 h-5 mx-auto mb-1" />
                                                <span className="text-[10px] uppercase tracking-wider">{channel.name}</span>
                                            </button>
                                        )
                                    })}
                                </div>
                            </div>

                            {/* Advanced Logic */}
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <label className="text-sm text-gray-400">Advanced Logic (Webhook Payload)</label>
                                    <span className="text-xs text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded">JSON</span>
                                </div>
                                <div className="bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg p-4 font-mono text-sm">
                                    <div className="text-gray-500">1</div>
                                    <pre className="text-gray-300 overflow-x-auto">
                                        {`{
  "event": "solar_flare_detected",
  "severity": "{{class}}",
  "timestamp": "auto"
}`}
                                    </pre>
                                </div>
                            </div>

                            {/* Save Button */}
                            <button className="w-full py-3 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 rounded-lg font-medium text-white transition-all">
                                Save Configuration
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer className="flex items-center justify-between py-6 border-t border-[#1a1a24] text-sm text-gray-600">
                <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded bg-[#1a1a24] flex items-center justify-center">
                        <span className="text-xs font-bold text-gray-500">Z</span>
                    </div>
                    <span>© 2024 ZERO-COMP Enterprise</span>
                </div>
                <div className="flex items-center space-x-6">
                    <a href="#" className="hover:text-white transition-colors">SYSTEM STATUS</a>
                    <a href="#" className="hover:text-white transition-colors">SECURITY</a>
                    <a href="#" className="hover:text-white transition-colors">GLOBAL NODES</a>
                </div>
            </footer>
        </div>
    )
}
