import { createSignal, Show, For } from 'solid-js'
import type { ArticlePlan } from '../lib/api'
import AnalysisCard from './AnalysisCard'
import BacktestCard from './BacktestCard'

interface PlanDrawerProps {
  isOpen: boolean
  onClose: () => void
  plan: ArticlePlan | null
  loading: boolean
}

type ViewMode = 'pro' | 'simple' | 'summary'

export default function PlanDrawer(props: PlanDrawerProps) {
  const [viewMode, setViewMode] = createSignal<ViewMode>('simple')

  return (
    <Show when={props.isOpen}>
      {/* Backdrop */}
      <div
        class="backdrop-glass z-40 animate-fade-in"
        onClick={props.onClose}
      />

      {/* Drawer */}
      <div
        class="fixed right-0 top-0 h-full w-full md:w-2/3 lg:w-1/2 drawer-glass shadow-glass-xl z-50 transform transition-all duration-500 ease-out overflow-y-auto scrollbar-thin translate-x-0"
      >
        {/* Header */}
        <div class="sticky top-0 bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 text-white p-6 shadow-glass-lg z-10 backdrop-blur-xl">
          <div class="flex justify-between items-center mb-4">
            <div>
              <h2 class="text-2xl font-bold mb-1">Trading Strategy Analysis</h2>
              <p class="text-blue-100 text-sm">AI-Powered Market Insights</p>
            </div>
            <button
              onClick={props.onClose}
              class="text-white hover:text-gray-200 text-3xl font-bold leading-none w-10 h-10 rounded-xl hover:bg-white/20 transition-all duration-200 flex items-center justify-center"
              aria-label="Close"
            >
              ×
            </button>
          </div>

          {/* View Mode Toggle */}
          <div class="flex gap-2">
            <button
              onClick={() => setViewMode('simple')}
              class={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
                viewMode() === 'simple'
                  ? 'bg-white text-blue-600 shadow-lg scale-105'
                  : 'bg-white/20 text-white hover:bg-white/30 backdrop-blur-md'
              }`}
            >
              Simple View
            </button>
            <button
              onClick={() => setViewMode('pro')}
              class={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
                viewMode() === 'pro'
                  ? 'bg-white text-blue-600 shadow-lg scale-105'
                  : 'bg-white/20 text-white hover:bg-white/30 backdrop-blur-md'
              }`}
            >
              Pro View
            </button>
            <button
              onClick={() => setViewMode('summary')}
              class={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
                viewMode() === 'summary'
                  ? 'bg-white text-blue-600 shadow-lg scale-105'
                  : 'bg-white/20 text-white hover:bg-white/30 backdrop-blur-md'
              }`}
            >
              Summary
            </button>
          </div>
        </div>

        {/* Content */}
        <div class="p-6">
          <Show when={props.loading}>
            <div class="flex flex-col items-center justify-center py-16">
              <div class="relative">
                <div class="spinner h-16 w-16 mb-4"></div>
                <div class="absolute inset-0 bg-blue-500/20 rounded-full blur-xl animate-pulse"></div>
              </div>
              <span class="mt-6 text-lg font-semibold text-gray-700 dark:text-gray-200">Analyzing article with AI...</span>
              <span class="mt-2 text-sm text-gray-500 dark:text-gray-400">This may take 30-60 seconds.</span>
              <div class="mt-6 flex gap-2">
                <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                <div class="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
              </div>
            </div>
          </Show>

          <Show when={!props.loading && props.plan}>
            {/* Educational Disclaimer */}
            <div class="bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border-l-4 border-yellow-400 dark:border-yellow-500 rounded-r-xl p-5 mb-6 shadow-glass backdrop-blur-sm">
              <div class="flex">
                <div class="flex-shrink-0">
                  <div class="w-10 h-10 rounded-xl bg-yellow-400 dark:bg-yellow-500 flex items-center justify-center">
                    <svg class="h-6 w-6 text-white" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                  </div>
                </div>
                <div class="ml-4">
                  <p class="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                    <strong class="font-bold">Educational Use Only:</strong> This analysis is generated by AI for educational purposes.
                    Not financial advice. Always do your own research and consult a licensed financial advisor.
                  </p>
                </div>
              </div>
            </div>

            {/* Summary View */}
            <Show when={viewMode() === 'summary'}>
              <div class="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-700 dark:to-gray-800 rounded-xl p-6 border-2 border-blue-200 dark:border-blue-700">
                <div class="flex items-start gap-3 mb-4">
                  <div class="flex-shrink-0 mt-1">
                    <svg class="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div class="flex-1">
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2">Quick Summary</h3>
                    <p class="text-gray-800 dark:text-gray-200 text-base leading-relaxed">
                      {props.plan?.llm_plan?.summary || 'No summary available.'}
                    </p>
                  </div>
                </div>
                <Show when={props.plan?.strategy_bucket}>
                  <div class="mt-4 pt-4 border-t border-blue-200 dark:border-blue-700">
                    <div class="flex items-center justify-between">
                      <span class="text-sm text-gray-600 dark:text-gray-400">Strategy:</span>
                      <span class="inline-block bg-blue-600 text-white px-3 py-1 rounded-lg text-sm font-medium">
                        {props.plan!.strategy_bucket}
                      </span>
                    </div>
                  </div>
                </Show>
              </div>
            </Show>

            {/* Simple View */}
            <Show when={viewMode() === 'simple'}>
              <div class="space-y-6">
                {/* Simple Explanation */}
                <div class="bg-gradient-to-br from-green-50 to-blue-50 dark:from-gray-700 dark:to-gray-800 rounded-xl p-6 border-2 border-green-200 dark:border-green-700">
                  <div class="flex items-start gap-3">
                    <div class="flex-shrink-0 mt-1">
                      <svg class="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                    <div class="flex-1">
                      <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-3">What This Means (Plain English)</h3>
                      <p class="text-gray-800 dark:text-gray-200 text-base leading-relaxed">
                        {props.plan?.llm_plan?.simple_explanation || 'No explanation available.'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Basic Info */}
                <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-5">
                  <h4 class="text-md font-semibold text-gray-900 dark:text-white mb-4">Basic Information</h4>
                  <div class="space-y-3">
                    <div class="flex justify-between items-center">
                      <span class="text-gray-600 dark:text-gray-400">Company:</span>
                      <span class="font-semibold text-gray-900 dark:text-white">
                        {props.plan?.llm_plan?.ticker || 'N/A'}
                      </span>
                    </div>
                    <div class="flex justify-between items-center">
                      <span class="text-gray-600 dark:text-gray-400">Industry:</span>
                      <span class="font-semibold text-gray-900 dark:text-white">
                        {props.plan?.llm_plan?.sector || 'N/A'}
                      </span>
                    </div>
                    <div class="flex justify-between items-center">
                      <span class="text-gray-600 dark:text-gray-400">Outlook:</span>
                      <span class={`font-semibold ${
                        props.plan?.llm_plan?.stance === 'BULLISH'
                          ? 'text-green-600 dark:text-green-400'
                          : props.plan?.llm_plan?.stance === 'BEARISH'
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-gray-600 dark:text-gray-400'
                      }`}>
                        {props.plan?.llm_plan?.stance === 'BULLISH' ? 'Positive ↑' :
                         props.plan?.llm_plan?.stance === 'BEARISH' ? 'Negative ↓' :
                         'Neutral →'}
                      </span>
                    </div>
                    <div class="flex justify-between items-center">
                      <span class="text-gray-600 dark:text-gray-400">AI Confidence:</span>
                      <span class="font-semibold text-gray-900 dark:text-white">
                        {props.plan?.strategy_risk?.confidence
                          ? `${(props.plan.strategy_risk.confidence * 100).toFixed(0)}%`
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* What to Watch */}
                <Show when={props.plan?.llm_plan?.risks && props.plan.llm_plan.risks.length > 0}>
                  <div class="bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800 p-5">
                    <h4 class="text-md font-semibold text-red-900 dark:text-red-200 mb-3">Things to Watch Out For</h4>
                    <ul class="space-y-2">
                      <For each={props.plan!.llm_plan!.risks}>
                        {(risk) => (
                          <li class="flex items-start gap-2">
                            <span class="text-red-600 dark:text-red-400 mt-0.5">⚠</span>
                            <span class="text-gray-800 dark:text-gray-200">{risk}</span>
                          </li>
                        )}
                      </For>
                    </ul>
                  </div>
                </Show>

                {/* Market Analysis Card */}
                <Show when={props.plan?.llm_plan?.ticker}>
                  <AnalysisCard
                    ticker={props.plan!.llm_plan!.ticker}
                    published={props.plan!.published_at || new Date().toISOString()}
                  />
                </Show>

                {/* Historical Backtest Card */}
                <Show when={props.plan?.llm_plan?.ticker}>
                  <BacktestCard
                    ticker={props.plan!.llm_plan!.ticker}
                    catalyst={props.plan!.llm_plan!.catalyst_type}
                  />
                </Show>
              </div>
            </Show>

            {/* Pro View */}
            <Show when={viewMode() === 'pro'}>
            {/* Strategy Bucket */}
            <Show when={props.plan?.strategy_bucket}>
              <div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Strategy Bucket</h3>
                <div class="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-4 py-2 rounded-lg font-medium">
                  {props.plan!.strategy_bucket}
                </div>
              </div>
            </Show>

            {/* Risk Parameters */}
            <Show when={props.plan?.strategy_risk}>
              <div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Risk Parameters</h3>
                <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-3">
                  <div class="flex justify-between items-center">
                    <span class="text-gray-600 dark:text-gray-300">Max Position Size:</span>
                    <span class="font-semibold text-gray-900 dark:text-white">
                      {(props.plan!.strategy_risk!.max_position_pct * 100).toFixed(2)}%
                    </span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-gray-600 dark:text-gray-300">Confidence:</span>
                    <span class="font-semibold text-gray-900 dark:text-white">
                      {(props.plan!.strategy_risk!.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-gray-600 dark:text-gray-300">Review In:</span>
                    <span class="font-semibold text-gray-900 dark:text-white">
                      {props.plan!.strategy_risk!.review_in_days} days
                    </span>
                  </div>
                  <div class="pt-2 border-t border-gray-200 dark:border-gray-600">
                    <span class="text-gray-600 dark:text-gray-300 block mb-1">Stop Guideline:</span>
                    <span class="text-sm text-gray-900 dark:text-white">
                      {props.plan!.strategy_risk!.stop_guideline}
                    </span>
                  </div>
                </div>
              </div>
            </Show>

            {/* LLM Plan Details */}
            <Show when={props.plan?.llm_plan}>
              <div class="space-y-6">
                {/* Ticker & Sector */}
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <h4 class="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">Ticker</h4>
                    <p class="text-lg font-bold text-gray-900 dark:text-white">
                      {props.plan!.llm_plan!.ticker || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <h4 class="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">Sector</h4>
                    <p class="text-lg font-bold text-gray-900 dark:text-white">
                      {props.plan!.llm_plan!.sector || 'N/A'}
                    </p>
                  </div>
                </div>

                {/* Catalyst & Stance */}
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <h4 class="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">Catalyst Type</h4>
                    <span class="inline-block bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 px-3 py-1 rounded text-sm font-medium">
                      {props.plan!.llm_plan!.catalyst_type}
                    </span>
                  </div>
                  <div>
                    <h4 class="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">Stance</h4>
                    <span class={`inline-block px-3 py-1 rounded text-sm font-medium ${
                      props.plan!.llm_plan!.stance === 'BULLISH' 
                        ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                        : props.plan!.llm_plan!.stance === 'BEARISH'
                        ? 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                    }`}>
                      {props.plan!.llm_plan!.stance}
                    </span>
                  </div>
                </div>

                {/* Thesis */}
                <div>
                  <h4 class="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">Thesis</h4>
                  <p class="text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    {props.plan!.llm_plan!.thesis}
                  </p>
                </div>

                {/* Key Facts */}
                <Show when={props.plan!.llm_plan!.key_facts && props.plan!.llm_plan!.key_facts.length > 0}>
                  <div>
                    <h4 class="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">Key Facts</h4>
                    <ul class="space-y-2">
                      <For each={props.plan!.llm_plan!.key_facts}>
                        {(fact) => (
                          <li class="flex items-start">
                            <span class="text-blue-600 dark:text-blue-400 mr-2">•</span>
                            <span class="text-gray-900 dark:text-white">{fact}</span>
                          </li>
                        )}
                      </For>
                    </ul>
                  </div>
                </Show>

                {/* Risks */}
                <Show when={props.plan!.llm_plan!.risks && props.plan!.llm_plan!.risks.length > 0}>
                  <div>
                    <h4 class="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">Risks</h4>
                    <ul class="space-y-2">
                      <For each={props.plan!.llm_plan!.risks}>
                        {(risk) => (
                          <li class="flex items-start">
                            <span class="text-red-600 dark:text-red-400 mr-2">⚠</span>
                            <span class="text-gray-900 dark:text-white">{risk}</span>
                          </li>
                        )}
                      </For>
                    </ul>
                  </div>
                </Show>

                {/* Suggested Setups */}
                <Show when={props.plan!.llm_plan!.suggested_setups && props.plan!.llm_plan!.suggested_setups.length > 0}>
                  <div>
                    <h4 class="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-3">Suggested Setups</h4>
                    <div class="space-y-3">
                      <For each={props.plan!.llm_plan!.suggested_setups}>
                        {(setup) => (
                          <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
                            <div class="flex items-center justify-between mb-2">
                              <span class="font-semibold text-gray-900 dark:text-white">{setup.style}</span>
                              <span class="text-sm text-gray-600 dark:text-gray-400">
                                Hold: {setup.hold_time_days} days
                              </span>
                            </div>
                            <div class="space-y-1 text-sm">
                              <div>
                                <span class="text-gray-600 dark:text-gray-400">Entry: </span>
                                <span class="text-gray-900 dark:text-white">{setup.entry_hint}</span>
                              </div>
                              <div>
                                <span class="text-gray-600 dark:text-gray-400">Invalidations: </span>
                                <span class="text-gray-900 dark:text-white">{setup.invalidations}</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </For>
                    </div>
                  </div>
                </Show>
              </div>
            </Show>
            </Show>

            <Show when={!props.loading && !props.plan}>
              <div class="text-center py-12 text-gray-500 dark:text-gray-400">
                No analysis available for this article.
              </div>
            </Show>
          </Show>
        </div>

        {/* Footer */}
        <div class="sticky bottom-0 bg-gray-100 dark:bg-gray-900 p-4 border-t border-gray-200 dark:border-gray-700">
          <p class="text-xs text-gray-500 dark:text-gray-400 text-center">
            Powered by News Tunneler • AI-Generated Analysis
          </p>
        </div>
      </div>
    </Show>
  )
}

