/**
 * ApexCharts Annotation Helpers
 * 
 * Utilities for adding event markers to running line charts.
 */

export type SignalAnnotation = {
  x: number; // timestamp in ms
  symbol: string;
  score: number;
  label: string;
  reasons: Array<{ k: string; v: any; "+": number }>;
};

/**
 * Create an ApexCharts annotation for a signal event.
 * 
 * @param signal - Signal data with timestamp, symbol, score, etc.
 * @returns ApexCharts annotation object
 */
export function createSignalAnnotation(signal: SignalAnnotation) {
  const color = getAnnotationColor(signal.label);
  
  return {
    x: signal.x,
    borderColor: color,
    label: {
      borderColor: color,
      style: {
        color: "#fff",
        background: color,
      },
      text: `${signal.symbol} ${signal.score.toFixed(0)}`,
    },
  };
}

/**
 * Get annotation color based on signal label.
 */
function getAnnotationColor(label: string): string {
  switch (label) {
    case "High-Conviction":
      return "#10b981"; // green-500
    case "Opportunity":
      return "#f59e0b"; // yellow-500
    case "Watch":
      return "#3b82f6"; // blue-500
    default:
      return "#6b7280"; // gray-500
  }
}

/**
 * Create a tooltip for a signal annotation.
 * 
 * @param signal - Signal data
 * @returns HTML string for tooltip
 */
export function createSignalTooltip(signal: SignalAnnotation): string {
  const topReasons = signal.reasons
    .sort((a, b) => Math.abs(b["+"]) - Math.abs(a["+"]))
    .slice(0, 3);
  
  const reasonsHtml = topReasons
    .map(
      (r) =>
        `<div style="display: flex; justify-content: space-between; margin: 4px 0;">
          <span>${r.k}:</span>
          <span style="color: ${r["+"] > 0 ? "#10b981" : "#ef4444"}; font-weight: bold;">
            ${r["+"] > 0 ? "+" : ""}${r["+"].toFixed(1)}
          </span>
        </div>`
    )
    .join("");
  
  return `
    <div style="padding: 8px; min-width: 200px;">
      <div style="font-weight: bold; margin-bottom: 8px;">
        ${signal.symbol} - ${signal.label}
      </div>
      <div style="font-size: 24px; font-weight: bold; margin-bottom: 8px;">
        ${signal.score.toFixed(1)}
      </div>
      <div style="font-size: 12px; color: #6b7280; margin-bottom: 8px;">
        Top Factors:
      </div>
      ${reasonsHtml}
    </div>
  `;
}

/**
 * Add signal annotations to ApexCharts options.
 * 
 * @param options - Existing ApexCharts options
 * @param signals - Array of signal annotations
 * @returns Updated options with annotations
 */
export function addSignalAnnotations(
  options: any,
  signals: SignalAnnotation[]
): any {
  const annotations = signals.map(createSignalAnnotation);
  
  return {
    ...options,
    annotations: {
      ...options.annotations,
      xaxis: [
        ...(options.annotations?.xaxis || []),
        ...annotations,
      ],
    },
  };
}

