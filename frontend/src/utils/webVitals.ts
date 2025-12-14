/**
 * Web Vitals monitoring utility
 * Tracks Core Web Vitals (LCP, INP, CLS) and reports to analytics
 */

import { onCLS, onLCP, onFCP, onTTFB, onINP, type Metric } from "web-vitals";

interface AnalyticsEvent {
  name: string;
  value: number;
  rating: "good" | "needs-improvement" | "poor";
  delta: number;
  id: string;
}

// Send metrics to analytics (customize this for your analytics provider)
function sendToAnalytics(metric: AnalyticsEvent) {
  // Log to console in development
  if (import.meta.env.DEV) {
    console.log(`[Web Vitals] ${metric.name}:`, {
      value: Math.round(metric.value),
      rating: metric.rating,
      delta: Math.round(metric.delta),
    });
  }

  // Send to vercel analytics if available
  if (window.va) {
    window.va("event", {
      name: metric.name,
      data: {
        value: Math.round(metric.value),
        rating: metric.rating,
      },
    });
  }
}

function getMetricRating(
  name: string,
  value: number
): "good" | "needs-improvement" | "poor" {
  const thresholds = {
    LCP: { good: 2500, poor: 4000 },
    CLS: { good: 0.1, poor: 0.25 },
    FCP: { good: 1800, poor: 3000 },
    TTFB: { good: 800, poor: 1800 },
    INP: { good: 200, poor: 500 },
  };

  const threshold = thresholds[name as keyof typeof thresholds];
  if (!threshold) return "good";

  if (value <= threshold.good) return "good";
  if (value <= threshold.poor) return "needs-improvement";
  return "poor";
}

function handleMetric(metric: Metric) {
  const analyticsEvent: AnalyticsEvent = {
    name: metric.name,
    value: metric.value,
    rating: getMetricRating(metric.name, metric.value),
    delta: metric.delta,
    id: metric.id,
  };

  sendToAnalytics(analyticsEvent);
}

// Initialize Web Vitals monitoring
export function initWebVitals() {
  // Only run in browser environment
  if (typeof window === "undefined" || typeof document === "undefined") {
    return;
  }

  // Wait for document to be ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startMonitoring);
  } else {
    startMonitoring();
  }
}

function startMonitoring() {
  try {
    // Core Web Vitals
    onLCP(handleMetric); // Largest Contentful Paint
    onINP(handleMetric); // Interaction to Next Paint (replaces FID)
    onCLS(handleMetric); // Cumulative Layout Shift

    // Additional metrics
    onFCP(handleMetric); // First Contentful Paint
    onTTFB(handleMetric); // Time to First Byte
  } catch (error) {
    console.error("[Web Vitals] Failed to initialize:", error);
  }
}

// Declare global types for analytics
declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
    va?: (...args: any[]) => void;
  }
}
