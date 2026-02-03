'use client'

interface UseCasePillsProps {
    options: string[]
    selected: string[]
    onChange: (selected: string[]) => void
    multiSelect?: boolean
}

export function UseCasePills({ options, selected, onChange, multiSelect = true }: UseCasePillsProps) {
    const handleClick = (option: string) => {
        if (multiSelect) {
            if (selected.includes(option)) {
                onChange(selected.filter(s => s !== option))
            } else {
                onChange([...selected, option])
            }
        } else {
            onChange([option])
        }
    }

    return (
        <div className="flex flex-wrap gap-3">
            {options.map((option) => {
                const isSelected = selected.includes(option)
                return (
                    <button
                        key={option}
                        type="button"
                        onClick={() => handleClick(option)}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${isSelected
                                ? 'bg-blue-500 text-white border-2 border-blue-500'
                                : 'bg-transparent text-gray-300 border-2 border-gray-600 hover:border-gray-500'
                            }`}
                    >
                        {option}
                    </button>
                )
            })}
        </div>
    )
}
