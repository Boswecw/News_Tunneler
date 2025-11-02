/**
 * ResearchCard - Self-training ML prediction display
 * 
 * Shows model probability for 3-day positive return based on
 * article analysis features. Model continuously learns from
 * realized market outcomes.
 */
import { Component, createSignal, onMount, Show } from "solid-js";

interface PredictResponse {
  prob_up_3d: number;
  model_version: string;
  confidence: string;
}

interface ResearchCardProps {
  analysis: any;
  onFeedback?: (label: number) => void;
}

const ResearchCard: Component<ResearchCardProps> = (props) => {
  const [prediction, setPrediction] = createSignal<PredictResponse | null>(null);
  const [error, setError] = createSignal<string | null>(null);
  const [loading, setLoading] = createSignal(true);
  const [feedbackSent, setFeedbackSent] = createSignal(false);

  onMount(async () => {
    try {
      const apiBase = import.meta.env.VITE_API_BASE || "http://localhost:8000";
      const response = await fetch(`${apiBase}/research/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysis: props.analysis }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `HTTP ${response.status}`);
      }

      const data = await response.json();
      setPrediction(data);
    } catch (e: any) {
      console.error("Research prediction error:", e);
      setError(e.message || "Failed to get prediction");
    } finally {
      setLoading(false);
    }
  });

  const sendFeedback = async (label: number) => {
    try {
      const apiBase = import.meta.env.VITE_API_BASE || "http://localhost:8000";
      const response = await fetch(`${apiBase}/research/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analysis: props.analysis,
          label: label,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      setFeedbackSent(true);
      
      // Call optional callback
      if (props.onFeedback) {
        props.onFeedback(label);
      }

      // Reset feedback state after 3 seconds
      setTimeout(() => setFeedbackSent(false), 3000);
    } catch (e: any) {
      console.error("Feedback error:", e);
      setError("Failed to send feedback");
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case "High":
        return "text-green-700";
      case "Moderate":
        return "text-blue-700";
      case "Neutral":
        return "text-gray-700";
      case "Low":
        return "text-orange-700";
      case "Very Low":
        return "text-red-700";
      default:
        return "text-gray-700";
    }
  };

  const getProbabilityColor = (prob: number) => {
    if (prob >= 0.7) return "text-green-600";
    if (prob >= 0.55) return "text-blue-600";
    if (prob >= 0.45) return "text-gray-600";
    if (prob >= 0.3) return "text-orange-600";
    return "text-red-600";
  };

  return (
    <div class="w-full rounded-2xl border border-amber-300/30 bg-gradient-to-br from-amber-50/20 to-orange-50/10 px-4 py-3 shadow-sm backdrop-blur-sm">
      {/* Header */}
      <div class="flex items-center justify-between">
        <div class="text-xs tracking-wide text-amber-700 font-semibold uppercase">
          🧠 Research Model
        </div>
        <Show when={prediction()}>
          <div class="text-[10px] text-amber-600/70">
            {prediction()!.model_version}
          </div>
        </Show>
      </div>

      {/* Loading State */}
      <Show when={loading()}>
        <div class="mt-2 flex items-center gap-2">
          <div class="h-4 w-4 animate-spin rounded-full border-2 border-amber-600 border-t-transparent"></div>
          <div class="text-sm text-amber-700">Analyzing...</div>
        </div>
      </Show>

      {/* Error State */}
      <Show when={error() && !loading()}>
        <div class="mt-2 text-xs text-red-700 bg-red-50 rounded px-2 py-1">
          {error()}
        </div>
      </Show>

      {/* Prediction Display */}
      <Show when={prediction() && !loading()}>
        <div class="mt-2 space-y-2">
          {/* Probability */}
          <div class="flex items-baseline gap-2">
            <span class="text-xs text-amber-800/80">3-Day Outlook:</span>
            <span class={`text-lg font-bold ${getProbabilityColor(prediction()!.prob_up_3d)}`}>
              {(prediction()!.prob_up_3d * 100).toFixed(1)}%
            </span>
            <span class={`text-xs font-medium ${getConfidenceColor(prediction()!.confidence)}`}>
              ({prediction()!.confidence})
            </span>
          </div>

          {/* Interpretation */}
          <div class="text-xs text-amber-800/90 leading-relaxed">
            <Show when={prediction()!.prob_up_3d >= 0.6}>
              Model suggests <strong>elevated probability</strong> of positive 3-day return (&gt;1%).
            </Show>
            <Show when={prediction()!.prob_up_3d < 0.6 && prediction()!.prob_up_3d >= 0.4}>
              Model shows <strong>neutral outlook</strong> for 3-day movement.
            </Show>
            <Show when={prediction()!.prob_up_3d < 0.4}>
              Model suggests <strong>lower probability</strong> of positive 3-day return.
            </Show>
          </div>

          {/* Feedback Buttons */}
          <Show when={!feedbackSent()}>
            <div class="flex items-center gap-2 pt-1">
              <span class="text-[10px] text-amber-700/70">Your take:</span>
              <button
                onClick={() => sendFeedback(1)}
                class="px-2 py-0.5 text-[10px] font-medium text-green-700 bg-green-50 hover:bg-green-100 rounded border border-green-200 transition-colors"
                title="I think this will go up"
              >
                👍 Bullish
              </button>
              <button
                onClick={() => sendFeedback(0)}
                class="px-2 py-0.5 text-[10px] font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded border border-red-200 transition-colors"
                title="I think this will go down or stay flat"
              >
                👎 Bearish
              </button>
            </div>
          </Show>

          {/* Feedback Confirmation */}
          <Show when={feedbackSent()}>
            <div class="text-[10px] text-green-700 bg-green-50 rounded px-2 py-1">
              ✓ Thanks! Model updated with your feedback.
            </div>
          </Show>
        </div>
      </Show>

      {/* Disclaimer */}
      <div class="mt-2 pt-2 border-t border-amber-200/30">
        <div class="text-[10px] text-amber-800/70 leading-relaxed">
          <strong>Research context only.</strong> Self-training model for brainstorming.
          Not financial advice. Past performance ≠ future results.
        </div>
      </div>
    </div>
  );
};

export default ResearchCard;

