'use client'

interface ProgressBarProps {
    currentStep: number
    totalSteps: number
    label?: string
}

export function ProgressBar({ currentStep, totalSteps, label }: ProgressBarProps) {
    const percentage = Math.round((currentStep / totalSteps) * 100)

    return (
        <div className="w-full">
            <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-gray-400 font-medium">
                    STEP {currentStep} OF {totalSteps}
                </span>
                <div className="text-right">
                    {label && <div className="text-sm text-gray-400">{label}</div>}
                    <span className="text-sm font-semibold text-blue-400">{percentage}%</span>
                </div>
            </div>

            <div className="h-1 bg-gray-700/50 rounded-full overflow-hidden">
                <div
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all duration-500"
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    )
}
