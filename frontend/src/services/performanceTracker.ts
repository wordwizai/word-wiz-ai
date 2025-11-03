/**
 * Performance tracking for client-side phoneme processing.
 *
 * Tracks metrics such as:
 * - Time saved by client processing
 * - Success/failure rates
 * - Average processing times
 * - Model load times
 */

export interface ProcessingMetrics {
  /** Total number of client-side extractions attempted */
  clientExtractionsAttempted: number;
  /** Number of successful client extractions */
  clientExtractionsSucceeded: number;
  /** Number of failed client extractions (fell back to server) */
  clientExtractionsFailed: number;
  /** Total time saved by client processing (milliseconds) */
  timeSavedMs: number;
  /** Average client extraction time (milliseconds) */
  avgClientExtractionTimeMs: number;
  /** Average server extraction time (milliseconds) */
  avgServerExtractionTimeMs: number;
  /** Model load time (milliseconds) */
  modelLoadTimeMs: number | null;
  /** Total audio processed (seconds) */
  totalAudioProcessedSeconds: number;
}

export interface ProcessingEvent {
  /** Timestamp of the event */
  timestamp: number;
  /** Type of processing used */
  processingType: "client" | "server";
  /** Time taken in milliseconds */
  timeMs: number;
  /** Audio duration in seconds */
  audioDurationSeconds?: number;
  /** Whether it succeeded */
  success: boolean;
  /** Error message if failed */
  error?: string;
}

class PerformanceTracker {
  private static instance: PerformanceTracker | null = null;

  private metrics: ProcessingMetrics = {
    clientExtractionsAttempted: 0,
    clientExtractionsSucceeded: 0,
    clientExtractionsFailed: 0,
    timeSavedMs: 0,
    avgClientExtractionTimeMs: 0,
    avgServerExtractionTimeMs: 0,
    modelLoadTimeMs: null,
    totalAudioProcessedSeconds: 0,
  };

  private events: ProcessingEvent[] = [];
  private maxEvents = 100; // Keep last 100 events

  private constructor() {
    // Load metrics from localStorage if available
    this.loadMetrics();
  }

  static getInstance(): PerformanceTracker {
    if (!PerformanceTracker.instance) {
      PerformanceTracker.instance = new PerformanceTracker();
    }
    return PerformanceTracker.instance;
  }

  /**
   * Record a model load event.
   */
  recordModelLoad(timeMs: number): void {
    this.metrics.modelLoadTimeMs = timeMs;
    this.saveMetrics();

    console.log(`📊 Model loaded in ${(timeMs / 1000).toFixed(2)}s`);
  }

  /**
   * Record a client-side extraction attempt.
   */
  recordClientExtraction(
    timeMs: number,
    success: boolean,
    audioDurationSeconds?: number,
    error?: string
  ): void {
    this.metrics.clientExtractionsAttempted++;

    if (success) {
      this.metrics.clientExtractionsSucceeded++;

      // Update average client extraction time
      const totalSuccessful = this.metrics.clientExtractionsSucceeded;
      this.metrics.avgClientExtractionTimeMs =
        (this.metrics.avgClientExtractionTimeMs * (totalSuccessful - 1) +
          timeMs) /
        totalSuccessful;

      // Estimate time saved (assume server would take 3x longer)
      const estimatedServerTime = timeMs * 3;
      this.metrics.timeSavedMs += estimatedServerTime - timeMs;
    } else {
      this.metrics.clientExtractionsFailed++;
    }

    if (audioDurationSeconds) {
      this.metrics.totalAudioProcessedSeconds += audioDurationSeconds;
    }

    this.events.push({
      timestamp: Date.now(),
      processingType: "client",
      timeMs,
      audioDurationSeconds,
      success,
      error,
    });

    this.trimEvents();
    this.saveMetrics();

    if (success) {
      console.log(`✅ Client extraction: ${timeMs.toFixed(0)}ms`);
    } else {
      console.warn(`❌ Client extraction failed: ${error}`);
    }
  }

  /**
   * Record a server-side extraction.
   */
  recordServerExtraction(timeMs: number, audioDurationSeconds?: number): void {
    // Update average server extraction time
    const currentAvg = this.metrics.avgServerExtractionTimeMs;
    const totalEvents = this.events.filter(
      (e) => e.processingType === "server"
    ).length;
    this.metrics.avgServerExtractionTimeMs =
      (currentAvg * totalEvents + timeMs) / (totalEvents + 1);

    if (audioDurationSeconds) {
      this.metrics.totalAudioProcessedSeconds += audioDurationSeconds;
    }

    this.events.push({
      timestamp: Date.now(),
      processingType: "server",
      timeMs,
      audioDurationSeconds,
      success: true,
    });

    this.trimEvents();
    this.saveMetrics();

    console.log(`🌐 Server extraction: ${timeMs.toFixed(0)}ms`);
  }

  /**
   * Get current metrics.
   */
  getMetrics(): ProcessingMetrics {
    return { ...this.metrics };
  }

  /**
   * Get recent events.
   */
  getRecentEvents(count: number = 10): ProcessingEvent[] {
    return this.events.slice(-count);
  }

  /**
   * Get success rate as a percentage.
   */
  getSuccessRate(): number {
    if (this.metrics.clientExtractionsAttempted === 0) {
      return 0;
    }
    return (
      (this.metrics.clientExtractionsSucceeded /
        this.metrics.clientExtractionsAttempted) *
      100
    );
  }

  /**
   * Get average time saved per extraction.
   */
  getAvgTimeSaved(): number {
    if (this.metrics.clientExtractionsSucceeded === 0) {
      return 0;
    }
    return this.metrics.timeSavedMs / this.metrics.clientExtractionsSucceeded;
  }

  /**
   * Get a summary report for logging.
   */
  getSummary(): string {
    const successRate = this.getSuccessRate();
    const avgTimeSaved = this.getAvgTimeSaved();
    const totalTimeSavedSeconds = this.metrics.timeSavedMs / 1000;

    return `
📊 Performance Summary:
- Client extractions: ${this.metrics.clientExtractionsSucceeded}/${
      this.metrics.clientExtractionsAttempted
    } (${successRate.toFixed(1)}% success)
- Avg client time: ${this.metrics.avgClientExtractionTimeMs.toFixed(0)}ms
- Avg server time: ${this.metrics.avgServerExtractionTimeMs.toFixed(0)}ms
- Time saved: ${totalTimeSavedSeconds.toFixed(1)}s total, ${(
      avgTimeSaved / 1000
    ).toFixed(2)}s per extraction
- Audio processed: ${this.metrics.totalAudioProcessedSeconds.toFixed(1)}s
- Model load time: ${
      this.metrics.modelLoadTimeMs
        ? (this.metrics.modelLoadTimeMs / 1000).toFixed(2) + "s"
        : "N/A"
    }
    `.trim();
  }

  /**
   * Log summary to console.
   */
  logSummary(): void {
    console.log(this.getSummary());
  }

  /**
   * Reset all metrics.
   */
  reset(): void {
    this.metrics = {
      clientExtractionsAttempted: 0,
      clientExtractionsSucceeded: 0,
      clientExtractionsFailed: 0,
      timeSavedMs: 0,
      avgClientExtractionTimeMs: 0,
      avgServerExtractionTimeMs: 0,
      modelLoadTimeMs: null,
      totalAudioProcessedSeconds: 0,
    };
    this.events = [];
    this.saveMetrics();

    console.log("📊 Performance metrics reset");
  }

  /**
   * Trim events to max size.
   */
  private trimEvents(): void {
    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(-this.maxEvents);
    }
  }

  /**
   * Save metrics to localStorage.
   */
  private saveMetrics(): void {
    try {
      localStorage.setItem(
        "phoneme_performance_metrics",
        JSON.stringify(this.metrics)
      );
      localStorage.setItem(
        "phoneme_performance_events",
        JSON.stringify(this.events)
      );
    } catch (error) {
      // localStorage might be disabled
      console.warn("Failed to save performance metrics:", error);
    }
  }

  /**
   * Load metrics from localStorage.
   */
  private loadMetrics(): void {
    try {
      const metricsJson = localStorage.getItem("phoneme_performance_metrics");
      const eventsJson = localStorage.getItem("phoneme_performance_events");

      if (metricsJson) {
        this.metrics = JSON.parse(metricsJson);
      }

      if (eventsJson) {
        this.events = JSON.parse(eventsJson);
      }
    } catch (error) {
      // Failed to load, use defaults
      console.warn("Failed to load performance metrics:", error);
    }
  }
}

// Export singleton instance
export const performanceTracker = PerformanceTracker.getInstance();

// Expose to window for debugging (development only)
if (import.meta.env.DEV) {
  (window as any).performanceTracker = performanceTracker;
}
