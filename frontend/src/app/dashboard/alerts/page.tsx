'use client'

import { useState } from 'react'
import {
    Plus,
    Link as LinkIcon,
    Mail,
    MessageSquare,
    Hash,
    Loader2,
    Trash2,
    AlertCircle
} from 'lucide-react'
import { useUserAlerts, CreateAlertConfig, AlertConfig, DeliveryChannels } from '@/lib/user-alerts'

const deliveryChannels = [
    { id: 'email', name: 'EMAIL', icon: Mail },
    { id: 'webhook', name: 'WEBHOOK', icon: LinkIcon },
    { id: 'discord', name: 'DISCORD', icon: MessageSquare },
    { id: 'slack', name: 'SLACK', icon: Hash },
]

const triggerSourceMap: Record<string, string> = {
    'flare_intensity': 'Flare Intensity',
    'kp_index': 'KP Index',
    'solar_wind': 'Solar Wind'
}

export default function AlertsPage() {
    const { alerts, loading, error, createAlert, toggleAlert, deleteAlert, refetch } = useUserAlerts()

    // Form state
    const [alertName, setAlertName] = useState('')
    const [triggerSource, setTriggerSource] = useState<'flare_intensity' | 'kp_index' | 'solar_wind'>('flare_intensity')
    const [condition, setCondition] = useState<'greater_than' | 'less_than' | 'equals'>('greater_than')
    const [threshold, setThreshold] = useState(70)
    const [selectedChannels, setSelectedChannels] = useState<DeliveryChannels>({
        email: true,
        webhook: false,
        discord: false,
        slack: false
    })
    const [webhookPayload, setWebhookPayload] = useState(`{
  "event": "solar_flare_detected",
  "severity": "{{class}}",
  "timestamp": "auto"
}`)
    const [saving, setSaving] = useState(false)
    const [saveError, setSaveError] = useState<string | null>(null)

    const toggleChannel = (channelId: keyof DeliveryChannels) => {
        setSelectedChannels(prev => ({
            ...prev,
            [channelId]: !prev[channelId]
        }))
    }

    const getThresholdLabel = () => {
        if (triggerSource === 'kp_index') {
            return { class: 'KP', value: (threshold / 10).toFixed(1) }
        }
        if (triggerSource === 'solar_wind') {
            return { class: 'km/s', value: Math.round(300 + (threshold * 7)).toString() }
        }
        // Flare intensity
        if (threshold < 33) return { class: 'C-Class', value: `C-${(threshold / 33 * 10).toFixed(1)}` }
        if (threshold < 66) return { class: 'M-Class', value: `M-${((threshold - 33) / 33 * 10).toFixed(1)}` }
        return { class: 'X-Class', value: `X-${((threshold - 66) / 34 * 10).toFixed(1)}` }
    }

    const thresholdInfo = getThresholdLabel()

    const handleSave = async () => {
        if (!alertName.trim()) {
            setSaveError('Alert name is required')
            return
        }

        setSaving(true)
        setSaveError(null)

        try {
            let parsedPayload = null
            try {
                parsedPayload = JSON.parse(webhookPayload)
            } catch {
                // Invalid JSON, ignore
            }

            const config: CreateAlertConfig = {
                name: alertName,
                trigger_source: triggerSource,
                condition: condition,
                threshold: threshold,
                delivery_channels: selectedChannels,
                webhook_payload: parsedPayload
            }

            await createAlert(config)

            // Reset form
            setAlertName('')
            setThreshold(70)
            setSelectedChannels({ email: true, webhook: false, discord: false, slack: false })

        } catch (err) {
            setSaveError(err instanceof Error ? err.message : 'Failed to create alert')
        } finally {
            setSaving(false)
        }
    }

    const handleToggle = async (alertId: string) => {
        try {
            await toggleAlert(alertId)
        } catch (err) {
            console.error('Toggle failed:', err)
        }
    }

    const handleDelete = async (alertId: string) => {
        if (!confirm('Are you sure you want to delete this alert?')) return

        try {
            await deleteAlert(alertId)
        } catch (err) {
            console.error('Delete failed:', err)
        }
    }

    const getTriggerDisplay = (alert: AlertConfig) => {
        const source = triggerSourceMap[alert.trigger_source] || alert.trigger_source
        const op = alert.condition === 'greater_than' ? '>' : alert.condition === 'less_than' ? '<' : '='
        return `${source} ${op} ${alert.threshold}`
    }

    const getTriggerColor = (alert: AlertConfig) => {
        if (alert.trigger_source === 'flare_intensity' && alert.threshold > 66) return 'red'
        if (alert.trigger_source === 'kp_index') return 'purple'
        return 'gray'
    }

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
                <button
                    onClick={() => document.getElementById('alert-name-input')?.focus()}
                    className="px-4 py-2 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 rounded-lg font-medium text-white flex items-center space-x-2 transition-all"
                >
                    <Plus className="w-4 h-4" />
                    <span>Create New Alert</span>
                </button>
            </div>

            <div className="grid grid-cols-12 gap-6">
                {/* Active Notifications Table */}
                <div className="col-span-12 lg:col-span-7">
                    <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl">
                        <div className="p-4 border-b border-[#2a2a3a] flex items-center justify-between">
                            <h2 className="text-lg font-semibold text-white">Active Notifications</h2>
                            {loading && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
                        </div>

                        {/* Table Header */}
                        <div className="grid grid-cols-12 gap-4 px-4 py-3 text-xs text-gray-500 uppercase tracking-wider border-b border-[#2a2a3a]">
                            <div className="col-span-4">Alert Name</div>
                            <div className="col-span-3">Trigger</div>
                            <div className="col-span-2">Delivery</div>
                            <div className="col-span-2 text-center">Status</div>
                            <div className="col-span-1"></div>
                        </div>

                        {/* Error State */}
                        {error && (
                            <div className="p-8 text-center">
                                <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
                                <p className="text-red-400">{error}</p>
                                <button
                                    onClick={refetch}
                                    className="mt-2 text-sm text-purple-400 hover:underline"
                                >
                                    Retry
                                </button>
                            </div>
                        )}

                        {/* Empty State */}
                        {!loading && !error && alerts.length === 0 && (
                            <div className="p-8 text-center text-gray-500">
                                <p>No alerts configured yet.</p>
                                <p className="text-sm mt-1">Create your first alert using the form.</p>
                            </div>
                        )}

                        {/* Table Body */}
                        <div className="divide-y divide-[#2a2a3a]">
                            {alerts.map((alert) => {
                                const triggerColor = getTriggerColor(alert)
                                return (
                                    <div key={alert.id} className="grid grid-cols-12 gap-4 px-4 py-4 items-center hover:bg-[#1a1a24] transition-colors">
                                        <div className="col-span-4">
                                            <div className="font-medium text-white">{alert.name}</div>
                                            <div className="text-xs text-gray-500">
                                                Triggered {alert.triggered_count} times
                                            </div>
                                        </div>
                                        <div className="col-span-3">
                                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-mono ${triggerColor === 'red' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                                                triggerColor === 'purple' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' :
                                                    'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                                                }`}>
                                                {getTriggerDisplay(alert)}
                                            </span>
                                        </div>
                                        <div className="col-span-2">
                                            <div className="flex items-center space-x-2">
                                                {alert.delivery_channels.webhook && (
                                                    <LinkIcon className="w-4 h-4 text-gray-400" />
                                                )}
                                                {alert.delivery_channels.email && (
                                                    <Mail className="w-4 h-4 text-gray-400" />
                                                )}
                                                {alert.delivery_channels.discord && (
                                                    <MessageSquare className="w-4 h-4 text-gray-400" />
                                                )}
                                                {alert.delivery_channels.slack && (
                                                    <Hash className="w-4 h-4 text-gray-400" />
                                                )}
                                            </div>
                                        </div>
                                        <div className="col-span-2 flex justify-center">
                                            <button
                                                onClick={() => handleToggle(alert.id)}
                                                className={`relative w-12 h-6 rounded-full transition-colors ${alert.is_active ? 'bg-purple-600' : 'bg-[#2a2a3a]'
                                                    }`}
                                            >
                                                <span className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${alert.is_active ? 'left-7' : 'left-1'
                                                    }`} />
                                            </button>
                                        </div>
                                        <div className="col-span-1 flex justify-end">
                                            <button
                                                onClick={() => handleDelete(alert.id)}
                                                className="p-1 text-gray-500 hover:text-red-400 transition-colors"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                )
                            })}
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
                                    id="alert-name-input"
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
                                        onChange={(e) => setTriggerSource(e.target.value as typeof triggerSource)}
                                        className="w-full px-4 py-3 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white focus:border-purple-500 focus:outline-none transition-colors appearance-none"
                                    >
                                        <option value="flare_intensity">Flare Intensity</option>
                                        <option value="kp_index">KP Index</option>
                                        <option value="solar_wind">Solar Wind</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">Condition</label>
                                    <select
                                        value={condition}
                                        onChange={(e) => setCondition(e.target.value as typeof condition)}
                                        className="w-full px-4 py-3 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white focus:border-purple-500 focus:outline-none transition-colors appearance-none"
                                    >
                                        <option value="greater_than">Greater than</option>
                                        <option value="less_than">Less than</option>
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
                                {triggerSource === 'flare_intensity' && (
                                    <div className="flex justify-between text-xs text-gray-600 mt-1">
                                        <span>C-CLASS</span>
                                        <span>M-CLASS</span>
                                        <span>X-CLASS</span>
                                    </div>
                                )}
                            </div>

                            {/* Delivery Channels */}
                            <div>
                                <label className="block text-sm text-gray-400 mb-3">Delivery Channels</label>
                                <div className="grid grid-cols-4 gap-2">
                                    {deliveryChannels.map((channel) => {
                                        const Icon = channel.icon
                                        const isSelected = selectedChannels[channel.id as keyof DeliveryChannels]
                                        return (
                                            <button
                                                key={channel.id}
                                                onClick={() => toggleChannel(channel.id as keyof DeliveryChannels)}
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
                                <textarea
                                    value={webhookPayload}
                                    onChange={(e) => setWebhookPayload(e.target.value)}
                                    className="w-full h-32 px-4 py-3 bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg font-mono text-sm text-gray-300 focus:border-purple-500 focus:outline-none transition-colors resize-none"
                                />
                            </div>

                            {/* Error Message */}
                            {saveError && (
                                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                    {saveError}
                                </div>
                            )}

                            {/* Save Button */}
                            <button
                                onClick={handleSave}
                                disabled={saving}
                                className="w-full py-3 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium text-white transition-all flex items-center justify-center space-x-2"
                            >
                                {saving ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        <span>Saving...</span>
                                    </>
                                ) : (
                                    <span>Save Configuration</span>
                                )}
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
