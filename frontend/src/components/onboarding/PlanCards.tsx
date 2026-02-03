'use client'

import { Check } from 'lucide-react'

interface Plan {
    id: string
    name: string
    price: string
    period: string
    features: string[]
    recommended?: boolean
    buttonText: string
}

interface PlanCardsProps {
    plans: Plan[]
    selectedPlan: string
    onSelect: (planId: string) => void
}

export function PlanCards({ plans, selectedPlan, onSelect }: PlanCardsProps) {
    return (
        <div className="grid md:grid-cols-2 gap-4">
            {plans.map((plan) => {
                const isSelected = selectedPlan === plan.id
                return (
                    <div
                        key={plan.id}
                        className={`relative rounded-2xl p-6 transition-all cursor-pointer ${plan.recommended
                                ? 'bg-gray-800/80 border-2 border-blue-500'
                                : 'bg-gray-800/50 border-2 border-gray-700 hover:border-gray-600'
                            } ${isSelected ? 'ring-2 ring-blue-500 ring-offset-2 ring-offset-[#0B1120]' : ''}`}
                        onClick={() => onSelect(plan.id)}
                    >
                        {/* Recommended Badge */}
                        {plan.recommended && (
                            <div className="absolute -top-3 right-4">
                                <span className="px-3 py-1 bg-blue-500 text-white text-xs font-bold rounded-full uppercase tracking-wider">
                                    Recommended
                                </span>
                            </div>
                        )}

                        {/* Plan Header */}
                        <div className="mb-4">
                            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
                                {plan.name}
                            </div>
                            <div className="flex items-baseline gap-1">
                                <span className="text-3xl font-bold text-white">{plan.price}</span>
                                <span className="text-gray-400 text-sm">{plan.period}</span>
                            </div>
                        </div>

                        {/* Features */}
                        <ul className="space-y-3 mb-6">
                            {plan.features.map((feature, index) => (
                                <li key={index} className="flex items-center gap-3 text-sm text-gray-300">
                                    <Check className={`w-4 h-4 flex-shrink-0 ${plan.recommended ? 'text-blue-400' : 'text-green-400'}`} />
                                    {feature}
                                </li>
                            ))}
                        </ul>

                        {/* Select Button */}
                        <button
                            type="button"
                            onClick={() => onSelect(plan.id)}
                            className={`w-full py-3 rounded-xl font-medium transition-all ${plan.recommended
                                    ? 'bg-blue-500 hover:bg-blue-600 text-white'
                                    : 'bg-gray-700 hover:bg-gray-600 text-white'
                                }`}
                        >
                            {plan.buttonText}
                        </button>
                    </div>
                )
            })}
        </div>
    )
}

// Default plans data
export const defaultPlans: Plan[] = [
    {
        id: 'standard',
        name: 'STANDARD',
        price: '$0',
        period: 'forever',
        features: [
            'Standard Data Access',
            'Basic CSV Exports',
            'Community Support'
        ],
        buttonText: 'Select Standard'
    },
    {
        id: 'pro',
        name: 'PRO PERFORMANCE',
        price: 'Free',
        period: 'for 7 days',
        features: [
            'Advanced Analytics Engine',
            'Real-time API Feeds',
            'Priority Support (24h)',
            'Custom White-label Reports'
        ],
        recommended: true,
        buttonText: 'Start Pro Trial'
    }
]
