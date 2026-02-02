'use client'

import { useState } from 'react'
import {
    Key,
    Copy,
    RefreshCw,
    Trash2,
    Eye,
    EyeOff,
    Shield,
    Zap,
    BarChart3,
    Check
} from 'lucide-react'

export default function SettingsPage() {
    const [showApiKey, setShowApiKey] = useState(false)
    const [copied, setCopied] = useState(false)

    // Mock API key
    const apiKey = 'zc_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'
    const maskedKey = 'zc_live_••••••••••••••••••••••••p6'

    const copyToClipboard = () => {
        navigator.clipboard.writeText(apiKey)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className="max-w-4xl space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-white">Settings</h1>
                <p className="text-gray-500 mt-1">
                    Manage your API keys and account settings.
                </p>
            </div>

            {/* API Key Section */}
            <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-6">
                <div className="flex items-center space-x-3 mb-6">
                    <div className="p-2 bg-purple-600/20 rounded-lg">
                        <Key className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-white">API Key</h2>
                        <p className="text-sm text-gray-500">Your secret key for API authentication</p>
                    </div>
                </div>

                {/* Key Display */}
                <div className="flex items-center space-x-3 mb-4">
                    <div className="flex-1 px-4 py-3 bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg font-mono text-sm">
                        <span className="text-gray-300">
                            {showApiKey ? apiKey : maskedKey}
                        </span>
                    </div>
                    <button
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="p-3 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-gray-400 hover:text-white transition-colors"
                    >
                        {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                    <button
                        onClick={copyToClipboard}
                        className="p-3 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-gray-400 hover:text-white transition-colors"
                    >
                        {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                    </button>
                </div>

                {/* Key Actions */}
                <div className="flex items-center space-x-3">
                    <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium text-white flex items-center space-x-2 transition-colors">
                        <RefreshCw className="w-4 h-4" />
                        <span>Regenerate Key</span>
                    </button>
                    <button className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 rounded-lg text-sm font-medium text-red-400 flex items-center space-x-2 transition-colors">
                        <Trash2 className="w-4 h-4" />
                        <span>Revoke Key</span>
                    </button>
                </div>

                <p className="text-xs text-gray-600 mt-4">
                    ⚠️ Keep your API key secret. Do not share it in public repositories or client-side code.
                </p>
            </div>

            {/* Usage Statistics */}
            <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-6">
                <div className="flex items-center space-x-3 mb-6">
                    <div className="p-2 bg-cyan-600/20 rounded-lg">
                        <BarChart3 className="w-5 h-5 text-cyan-400" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-white">Usage Statistics</h2>
                        <p className="text-sm text-gray-500">Current billing period usage</p>
                    </div>
                </div>

                <div className="grid grid-cols-3 gap-6">
                    <div className="bg-[#1a1a24] rounded-xl p-4">
                        <div className="text-xs text-gray-500 uppercase mb-2">API Requests</div>
                        <div className="text-2xl font-bold text-white">24,567</div>
                        <div className="mt-2 h-1.5 bg-[#2a2a3a] rounded-full overflow-hidden">
                            <div className="h-full w-[45%] bg-gradient-to-r from-purple-600 to-purple-400 rounded-full" />
                        </div>
                        <div className="text-xs text-gray-500 mt-1">of 50,000</div>
                    </div>

                    <div className="bg-[#1a1a24] rounded-xl p-4">
                        <div className="text-xs text-gray-500 uppercase mb-2">Webhooks Sent</div>
                        <div className="text-2xl font-bold text-white">1,234</div>
                        <div className="mt-2 h-1.5 bg-[#2a2a3a] rounded-full overflow-hidden">
                            <div className="h-full w-[25%] bg-gradient-to-r from-cyan-600 to-cyan-400 rounded-full" />
                        </div>
                        <div className="text-xs text-gray-500 mt-1">of 5,000</div>
                    </div>

                    <div className="bg-[#1a1a24] rounded-xl p-4">
                        <div className="text-xs text-gray-500 uppercase mb-2">Active Alerts</div>
                        <div className="text-2xl font-bold text-white">3</div>
                        <div className="mt-2 h-1.5 bg-[#2a2a3a] rounded-full overflow-hidden">
                            <div className="h-full w-[30%] bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full" />
                        </div>
                        <div className="text-xs text-gray-500 mt-1">of 10</div>
                    </div>
                </div>
            </div>

            {/* Subscription Tier */}
            <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                        <div className="p-2 bg-emerald-600/20 rounded-lg">
                            <Zap className="w-5 h-5 text-emerald-400" />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Current Plan</h2>
                            <p className="text-sm text-gray-500">Manage your subscription</p>
                        </div>
                    </div>
                    <span className="px-3 py-1 bg-purple-600/20 text-purple-400 text-sm font-medium rounded-full border border-purple-500/30">
                        PRO
                    </span>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-[#1a1a24] rounded-lg p-4">
                        <div className="text-xs text-gray-500 uppercase mb-1">Monthly Cost</div>
                        <div className="text-xl font-bold text-white">$50.00</div>
                    </div>
                    <div className="bg-[#1a1a24] rounded-lg p-4">
                        <div className="text-xs text-gray-500 uppercase mb-1">Next Billing</div>
                        <div className="text-xl font-bold text-white">Mar 1, 2026</div>
                    </div>
                </div>

                <div className="flex items-center space-x-3">
                    <button className="px-4 py-2 bg-[#1a1a24] hover:bg-[#252530] border border-[#2a2a3a] rounded-lg text-sm font-medium text-white transition-colors">
                        Upgrade to Enterprise
                    </button>
                    <button className="px-4 py-2 text-sm text-gray-500 hover:text-white transition-colors">
                        View billing history
                    </button>
                </div>
            </div>

            {/* Security */}
            <div className="bg-[#12121a] border border-[#2a2a3a] rounded-xl p-6">
                <div className="flex items-center space-x-3 mb-6">
                    <div className="p-2 bg-amber-600/20 rounded-lg">
                        <Shield className="w-5 h-5 text-amber-400" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-white">Security</h2>
                        <p className="text-sm text-gray-500">Protect your account</p>
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-[#1a1a24] rounded-lg">
                        <div>
                            <div className="font-medium text-white">Two-Factor Authentication</div>
                            <div className="text-sm text-gray-500">Add an extra layer of security</div>
                        </div>
                        <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium text-white transition-colors">
                            Enable
                        </button>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-[#1a1a24] rounded-lg">
                        <div>
                            <div className="font-medium text-white">IP Allowlist</div>
                            <div className="text-sm text-gray-500">Restrict API access to specific IPs</div>
                        </div>
                        <button className="px-4 py-2 bg-[#252530] hover:bg-[#2a2a3a] rounded-lg text-sm font-medium text-gray-400 hover:text-white transition-colors">
                            Configure
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
