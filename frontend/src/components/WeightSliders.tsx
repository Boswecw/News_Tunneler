import { createSignal, For } from 'solid-js'
import type { Settings } from '../lib/store'

interface WeightSlidersProps {
  settings: Settings
  onChange: (key: string, value: number) => void
}

const weights = [
  { key: 'weight_catalyst', label: 'Catalyst Weight', description: 'Impact of news catalyst' },
  { key: 'weight_novelty', label: 'Novelty Weight', description: 'Impact of article age' },
  { key: 'weight_credibility', label: 'Credibility Weight', description: 'Impact of source credibility' },
  { key: 'weight_sentiment', label: 'Sentiment Weight', description: 'Impact of sentiment analysis' },
  { key: 'weight_liquidity', label: 'Liquidity Weight', description: 'Impact of trading volume' },
]

export default function WeightSliders(props: WeightSlidersProps) {
  return (
    <div class="space-y-6">
      <For each={weights}>
        {(weight) => (
          <div>
            <div class="flex items-center justify-between mb-2">
              <div>
                <label class="label mb-0">{weight.label}</label>
                <p class="text-sm text-gray-600 dark:text-gray-400">{weight.description}</p>
              </div>
              <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {(props.settings[weight.key as keyof Settings] as number).toFixed(1)}
              </div>
            </div>
            <input
              type="range"
              min="0"
              max="5"
              step="0.1"
              value={props.settings[weight.key as keyof Settings] as number}
              onChange={(e) => props.onChange(weight.key, parseFloat(e.currentTarget.value))}
              class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
            <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>0</span>
              <span>5</span>
            </div>
          </div>
        )}
      </For>
    </div>
  )
}

