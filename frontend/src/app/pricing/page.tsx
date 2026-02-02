'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
    Check,
    Zap,
    Building2,
    Rocket,
    ArrowRight,
    Shield,
    Globe,
    Clock,
    Loader2
} from 'lucide-react'

const tiers = [
    {
        name: 'Free',
        price: '$0',
        period: 'forever',
        description: 'For exploring and development',
        icon: Zap,
        color: 'gray',
        features: [
            'Dashboard access',
            '100 API calls/day',
            '24-hour prediction history',
            'Community support',
            'Basic alerts (email only)',
        ],
        limitations: [
            'No WebSocket access',
            'No CSV export',
            'No custom webhooks',
        ],
        cta: 'Get Started',
        popular: false
    },
    {
        name: 'Pro',
        price: '$50',
        period: '/month',
        description: 'For production applications',
        icon: Rocket,
        color: 'purple',
        features: [
            'Everything in Free, plus:',
            '10,000 API calls/day',
            '30-day prediction history',
            'WebSocket real-time alerts',
            'Webhook integrations',
            'CSV data export',
            'Priority email support',
            'API key management',
        ],
        limitations: [],
        cta: 'Start Free Trial',
        popular: true
    },
    {
        name: 'Enterprise',
        price: '$500',
        period: '/month',
        description: 'For mission-critical operations',
        icon: Building2,
        color: 'cyan',
        features: [
            'Everything in Pro, plus:',
            'Unlimited API calls',
            '1-year historical data',
            'Multi-region redundancy',
            'Custom prediction models',
            'SLA guarantee (99.9%)',
            'Dedicated support engineer',
            'SSO/SAML integration',
            'Custom contracts available',
        ],
        limitations: [],
        cta: 'Contact Sales',
        popular: false
    }
]

export default function PricingPage() {
    const [annual, setAnnual] = useState(false)
    const [loadingTier, setLoadingTier] = useState<string | null>(null)

    const handleSelectPlan = async (tierName: string) => {
        if (tierName === 'Free') {
            window.location.href = '/auth/signup'
            return
        }

        if (tierName === 'Enterprise') {
            window.location.href = 'mailto:sales@zero-comp.com?subject=Enterprise%20Inquiry'
            return
        }

        setLoadingTier(tierName)
        // In production, this would initiate Razorpay checkout
        await new Promise(resolve => setTimeout(resolve, 1500))
        window.location.href = '/auth/signup?plan=pro'
    }

    return (
        <div className="min-h-screen bg-[#0a0a0f]">
            {/* Header */}
            <header className="border-b border-[#1a1a24]">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/" className="flex items-center space-x-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-cyan-500 flex items-center justify-center">
                            <span className="text-sm font-bold text-white">Z</span>
                        </div>
                        <span className="text-lg font-semibold text-white">ZERO-COMP</span>
                    </Link>
                    <Link
                        href="/auth/login"
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        Sign In
                    </Link>
                </div>
            </header>

            {/* Hero */}
            <section className="py-20 px-6 text-center">
                <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
                    Simple, Transparent Pricing
                </h1>
                <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-8">
                    Start free, scale as you grow. No hidden fees.
                </p>

                {/* Annual Toggle */}
                <div className="flex items-center justify-center space-x-4 mb-12">
                    <span className={`text-sm ${!annual ? 'text-white' : 'text-gray-500'}`}>Monthly</span>
                    <button
                        onClick={() => setAnnual(!annual)}
                        className={`relative w-14 h-7 rounded-full transition-colors ${annual ? 'bg-purple-600' : 'bg-[#2a2a3a]'}`}
                    >
                        <span className={`absolute top-1 w-5 h-5 rounded-full bg-white transition-transform ${annual ? 'left-8' : 'left-1'}`} />
                    </button>
                    <span className={`text-sm ${annual ? 'text-white' : 'text-gray-500'}`}>
                        Annual
                        <span className="ml-2 text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">Save 20%</span>
                    </span>
                </div>
            </section>

            {/* Pricing Cards */}
            <section className="max-w-6xl mx-auto px-6 pb-20">
                <div className="grid md:grid-cols-3 gap-6">
                    {tiers.map((tier) => {
                        const Icon = tier.icon
                        const price = annual && tier.price !== '$0'
                            ? `$${Math.round(parseInt(tier.price.slice(1)) * 0.8 * 12)}`
                            : tier.price
                        const period = annual && tier.price !== '$0' ? '/year' : tier.period

                        return (
                            <div
                                key={tier.name}
                                className={`relative bg-[#12121a] border rounded-2xl p-8 ${tier.popular
                                    ? 'border-purple-500 ring-1 ring-purple-500/20'
                                    : 'border-[#2a2a3a]'
                                    }`}
                            >
                                {tier.popular && (
                                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                        <span className="bg-gradient-to-r from-purple-600 to-cyan-500 text-white text-xs font-medium px-3 py-1 rounded-full">
                                            Most Popular
                                        </span>
                                    </div>
                                )}

                                <div className={`w-12 h-12 rounded-xl mb-4 flex items-center justify-center ${tier.color === 'purple' ? 'bg-purple-600/20' :
                                    tier.color === 'cyan' ? 'bg-cyan-600/20' :
                                        'bg-gray-600/20'
                                    }`}>
                                    <Icon className={`w-6 h-6 ${tier.color === 'purple' ? 'text-purple-400' :
                                        tier.color === 'cyan' ? 'text-cyan-400' :
                                            'text-gray-400'
                                        }`} />
                                </div>

                                <h3 className="text-xl font-bold text-white mb-1">{tier.name}</h3>
                                <p className="text-gray-500 text-sm mb-4">{tier.description}</p>

                                <div className="mb-6">
                                    <span className="text-4xl font-bold text-white">{price}</span>
                                    <span className="text-gray-500">{period}</span>
                                </div>

                                <button
                                    onClick={() => handleSelectPlan(tier.name)}
                                    disabled={loadingTier === tier.name}
                                    className={`w-full py-3 rounded-xl font-medium transition-all flex items-center justify-center space-x-2 ${tier.popular
                                        ? 'bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white'
                                        : 'bg-[#1a1a24] border border-[#2a2a3a] text-white hover:border-gray-600'
                                        }`}
                                >
                                    {loadingTier === tier.name ? (
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                    ) : (
                                        <>
                                            <span>{tier.cta}</span>
                                            <ArrowRight className="w-4 h-4" />
                                        </>
                                    )}
                                </button>

                                <div className="mt-6 pt-6 border-t border-[#2a2a3a]">
                                    <ul className="space-y-3">
                                        {tier.features.map((feature, idx) => (
                                            <li key={idx} className="flex items-start space-x-2 text-sm">
                                                <Check className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                                                <span className="text-gray-300">{feature}</span>
                                            </li>
                                        ))}
                                        {tier.limitations.map((limitation, idx) => (
                                            <li key={idx} className="flex items-start space-x-2 text-sm opacity-50">
                                                <span className="w-4 h-4 flex-shrink-0 text-center">-</span>
                                                <span className="text-gray-500 line-through">{limitation}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </section>

            {/* Trust Badges */}
            <section className="border-t border-[#1a1a24] py-16 px-6">
                <div className="max-w-4xl mx-auto">
                    <div className="grid grid-cols-3 gap-8 text-center">
                        <div>
                            <Shield className="w-8 h-8 text-purple-400 mx-auto mb-3" />
                            <h4 className="font-medium text-white mb-1">Enterprise Security</h4>
                            <p className="text-sm text-gray-500">SOC 2 Type II compliant</p>
                        </div>
                        <div>
                            <Globe className="w-8 h-8 text-cyan-400 mx-auto mb-3" />
                            <h4 className="font-medium text-white mb-1">Global Infrastructure</h4>
                            <p className="text-sm text-gray-500">Multi-region redundancy</p>
                        </div>
                        <div>
                            <Clock className="w-8 h-8 text-emerald-400 mx-auto mb-3" />
                            <h4 className="font-medium text-white mb-1">99.9% Uptime SLA</h4>
                            <p className="text-sm text-gray-500">For Enterprise customers</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* FAQ Preview */}
            <section className="border-t border-[#1a1a24] py-16 px-6 text-center">
                <h2 className="text-2xl font-bold text-white mb-4">Questions?</h2>
                <p className="text-gray-400 mb-6">
                    Contact us at{' '}
                    <a href="mailto:support@zero-comp.com" className="text-purple-400 hover:underline">
                        support@zero-comp.com
                    </a>
                </p>
            </section>

            {/* Footer */}
            <footer className="border-t border-[#1a1a24] py-8 px-6">
                <div className="max-w-7xl mx-auto flex items-center justify-between text-sm text-gray-500">
                    <p>© 2024 ZERO-COMP. All rights reserved.</p>
                    <div className="flex items-center space-x-6">
                        <a href="#" className="hover:text-white transition-colors">Privacy</a>
                        <a href="#" className="hover:text-white transition-colors">Terms</a>
                    </div>
                </div>
            </footer>
        </div>
    )
}
