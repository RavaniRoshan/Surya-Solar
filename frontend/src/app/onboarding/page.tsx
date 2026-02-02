'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
    Rocket,
    Satellite,
    Zap,
    Plane,
    Code2,
    Bell,
    Key,
    Check,
    ArrowRight,
    ArrowLeft,
    Copy,
    Loader2
} from 'lucide-react'

const useCases = [
    { id: 'satellite', name: 'Satellite Operations', icon: Satellite, description: 'Protect fleet assets from solar storms' },
    { id: 'power', name: 'Power Grid', icon: Zap, description: 'Prevent outages during geomagnetic events' },
    { id: 'aviation', name: 'Aviation', icon: Plane, description: 'Adjust polar routes for crew safety' },
    { id: 'developer', name: 'Developer', icon: Code2, description: 'Build space weather apps' },
]

const steps = [
    { id: 1, name: 'Welcome' },
    { id: 2, name: 'Use Case' },
    { id: 3, name: 'First Alert' },
    { id: 4, name: 'API Key' },
    { id: 5, name: 'Complete' },
]

export default function OnboardingPage() {
    const router = useRouter()
    const [currentStep, setCurrentStep] = useState(1)
    const [selectedUseCase, setSelectedUseCase] = useState<string | null>(null)
    const [alertName, setAlertName] = useState('')
    const [threshold, setThreshold] = useState(70)
    const [apiKey, setApiKey] = useState('')
    const [apiKeyCopied, setApiKeyCopied] = useState(false)
    const [loading, setLoading] = useState(false)

    const nextStep = () => {
        if (currentStep < 5) {
            setCurrentStep(prev => prev + 1)
        }
    }

    const prevStep = () => {
        if (currentStep > 1) {
            setCurrentStep(prev => prev - 1)
        }
    }

    const generateApiKey = async () => {
        setLoading(true)
        // Simulate API key generation
        await new Promise(resolve => setTimeout(resolve, 1500))
        const key = `zc_live_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`
        setApiKey(key)
        setLoading(false)
    }

    const copyApiKey = () => {
        navigator.clipboard.writeText(apiKey)
        setApiKeyCopied(true)
        setTimeout(() => setApiKeyCopied(false), 2000)
    }

    const finishOnboarding = () => {
        localStorage.setItem('onboarding_complete', 'true')
        router.push('/dashboard')
    }

    return (
        <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
            <div className="w-full max-w-2xl">
                {/* Progress Bar */}
                <div className="mb-8">
                    <div className="flex items-center justify-between mb-2">
                        {steps.map((step, idx) => (
                            <div key={step.id} className="flex items-center">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${currentStep >= step.id
                                    ? 'bg-purple-600 text-white'
                                    : 'bg-[#1a1a24] text-gray-500'
                                    }`}>
                                    {currentStep > step.id ? <Check className="w-4 h-4" /> : step.id}
                                </div>
                                {idx < steps.length - 1 && (
                                    <div className={`w-16 h-0.5 mx-2 ${currentStep > step.id ? 'bg-purple-600' : 'bg-[#2a2a3a]'}`} />
                                )}
                            </div>
                        ))}
                    </div>
                    <p className="text-center text-sm text-gray-500">{steps[currentStep - 1].name}</p>
                </div>

                {/* Card Container */}
                <div className="bg-[#12121a] border border-[#2a2a3a] rounded-2xl p-8">
                    {/* Step 1: Welcome */}
                    {currentStep === 1 && (
                        <div className="text-center space-y-6">
                            <div className="w-20 h-20 bg-gradient-to-br from-purple-600 to-cyan-500 rounded-2xl mx-auto flex items-center justify-center">
                                <Rocket className="w-10 h-10 text-white" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-white mb-2">Welcome to ZERO-COMP</h1>
                                <p className="text-gray-400 text-lg">
                                    Let&apos;s set up your solar weather monitoring in less than 2 minutes.
                                </p>
                            </div>
                            <div className="grid grid-cols-3 gap-4 pt-4">
                                <div className="bg-[#1a1a24] border border-[#2a2a3a] rounded-xl p-4 text-center">
                                    <p className="text-2xl font-bold text-cyan-400">10min</p>
                                    <p className="text-xs text-gray-500">Update Frequency</p>
                                </div>
                                <div className="bg-[#1a1a24] border border-[#2a2a3a] rounded-xl p-4 text-center">
                                    <p className="text-2xl font-bold text-purple-400">94%</p>
                                    <p className="text-xs text-gray-500">Prediction Accuracy</p>
                                </div>
                                <div className="bg-[#1a1a24] border border-[#2a2a3a] rounded-xl p-4 text-center">
                                    <p className="text-2xl font-bold text-emerald-400">24/7</p>
                                    <p className="text-xs text-gray-500">Monitoring</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Step 2: Use Case */}
                    {currentStep === 2 && (
                        <div className="space-y-6">
                            <div className="text-center">
                                <h2 className="text-2xl font-bold text-white mb-2">What brings you here?</h2>
                                <p className="text-gray-400">Help us customize your experience</p>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                {useCases.map((useCase) => {
                                    const Icon = useCase.icon
                                    const isSelected = selectedUseCase === useCase.id
                                    return (
                                        <button
                                            key={useCase.id}
                                            onClick={() => setSelectedUseCase(useCase.id)}
                                            className={`p-4 rounded-xl border text-left transition-all ${isSelected
                                                ? 'bg-purple-600/20 border-purple-500'
                                                : 'bg-[#1a1a24] border-[#2a2a3a] hover:border-gray-600'
                                                }`}
                                        >
                                            <Icon className={`w-8 h-8 mb-2 ${isSelected ? 'text-purple-400' : 'text-gray-400'}`} />
                                            <p className="font-medium text-white">{useCase.name}</p>
                                            <p className="text-xs text-gray-500 mt-1">{useCase.description}</p>
                                        </button>
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {/* Step 3: First Alert */}
                    {currentStep === 3 && (
                        <div className="space-y-6">
                            <div className="text-center">
                                <div className="w-12 h-12 bg-purple-600/20 rounded-xl mx-auto flex items-center justify-center mb-4">
                                    <Bell className="w-6 h-6 text-purple-400" />
                                </div>
                                <h2 className="text-2xl font-bold text-white mb-2">Create Your First Alert</h2>
                                <p className="text-gray-400">Get notified when solar activity reaches your threshold</p>
                            </div>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">Alert Name</label>
                                    <input
                                        type="text"
                                        value={alertName}
                                        onChange={(e) => setAlertName(e.target.value)}
                                        placeholder="e.g., Critical X-Class Alert"
                                        className="w-full px-4 py-3 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-white placeholder-gray-600 focus:border-purple-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <div className="flex justify-between mb-2">
                                        <label className="text-sm text-gray-400">Flare Intensity Threshold</label>
                                        <span className="text-sm text-red-400">
                                            {threshold < 33 ? 'C-Class' : threshold < 66 ? 'M-Class' : 'X-Class'}
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
                            </div>
                        </div>
                    )}

                    {/* Step 4: API Key */}
                    {currentStep === 4 && (
                        <div className="space-y-6">
                            <div className="text-center">
                                <div className="w-12 h-12 bg-cyan-600/20 rounded-xl mx-auto flex items-center justify-center mb-4">
                                    <Key className="w-6 h-6 text-cyan-400" />
                                </div>
                                <h2 className="text-2xl font-bold text-white mb-2">Your API Key</h2>
                                <p className="text-gray-400">Use this key for programmatic access</p>
                            </div>
                            {!apiKey ? (
                                <button
                                    onClick={generateApiKey}
                                    disabled={loading}
                                    className="w-full py-4 bg-gradient-to-r from-cyan-600 to-cyan-700 hover:from-cyan-700 hover:to-cyan-800 disabled:opacity-50 rounded-xl font-medium text-white transition-all flex items-center justify-center space-x-2"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            <span>Generating...</span>
                                        </>
                                    ) : (
                                        <>
                                            <Key className="w-5 h-5" />
                                            <span>Generate API Key</span>
                                        </>
                                    )}
                                </button>
                            ) : (
                                <div className="space-y-4">
                                    <div className="bg-[#0a0a0f] border border-[#2a2a3a] rounded-xl p-4">
                                        <div className="flex items-center justify-between">
                                            <code className="text-cyan-400 font-mono text-sm break-all">{apiKey}</code>
                                            <button
                                                onClick={copyApiKey}
                                                className="ml-4 p-2 hover:bg-[#1a1a24] rounded-lg transition-colors"
                                            >
                                                {apiKeyCopied ? (
                                                    <Check className="w-5 h-5 text-emerald-400" />
                                                ) : (
                                                    <Copy className="w-5 h-5 text-gray-400" />
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
                                        <p className="text-yellow-400 text-sm">
                                            ⚠️ <strong>Save this key now!</strong> It won&apos;t be shown again.
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Step 5: Complete */}
                    {currentStep === 5 && (
                        <div className="text-center space-y-6">
                            <div className="w-20 h-20 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-full mx-auto flex items-center justify-center">
                                <Check className="w-10 h-10 text-white" />
                            </div>
                            <div>
                                <h2 className="text-3xl font-bold text-white mb-2">You&apos;re All Set!</h2>
                                <p className="text-gray-400 text-lg">
                                    Welcome to the future of solar weather prediction
                                </p>
                            </div>
                            <div className="bg-[#1a1a24] border border-[#2a2a3a] rounded-xl p-6 text-left">
                                <h3 className="font-medium text-white mb-3">What&apos;s Next:</h3>
                                <ul className="space-y-2 text-gray-400">
                                    <li className="flex items-center space-x-2">
                                        <Check className="w-4 h-4 text-emerald-400" />
                                        <span>Your first alert is configured and active</span>
                                    </li>
                                    <li className="flex items-center space-x-2">
                                        <Check className="w-4 h-4 text-emerald-400" />
                                        <span>Real-time predictions are now available</span>
                                    </li>
                                    <li className="flex items-center space-x-2">
                                        <Check className="w-4 h-4 text-emerald-400" />
                                        <span>Check out the API docs to integrate</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    )}

                    {/* Navigation Buttons */}
                    <div className="flex items-center justify-between mt-8 pt-6 border-t border-[#2a2a3a]">
                        {currentStep > 1 && currentStep < 5 ? (
                            <button
                                onClick={prevStep}
                                className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
                            >
                                <ArrowLeft className="w-4 h-4" />
                                <span>Back</span>
                            </button>
                        ) : (
                            <div />
                        )}

                        {currentStep < 5 ? (
                            <button
                                onClick={nextStep}
                                disabled={currentStep === 2 && !selectedUseCase}
                                className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-medium text-white transition-all"
                            >
                                <span>{currentStep === 4 && !apiKey ? 'Skip' : 'Continue'}</span>
                                <ArrowRight className="w-4 h-4" />
                            </button>
                        ) : (
                            <button
                                onClick={finishOnboarding}
                                className="w-full py-3 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 rounded-xl font-medium text-white transition-all"
                            >
                                Go to Dashboard
                            </button>
                        )}
                    </div>
                </div>

                {/* Skip Link */}
                {currentStep < 5 && (
                    <div className="text-center mt-4">
                        <button
                            onClick={() => router.push('/dashboard')}
                            className="text-sm text-gray-500 hover:text-gray-400 transition-colors"
                        >
                            Skip onboarding
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
