/**
 * Network quality detection for optimizing client-side processing decisions.
 *
 * Uses the Network Information API to detect connection quality and
 * make intelligent decisions about whether to use client-side processing.
 */

export interface NetworkInfo {
  /** Effective connection type (4g, 3g, 2g, slow-2g) */
  effectiveType: string;
  /** Downlink speed in Mbps */
  downlink?: number;
  /** Round-trip time in ms */
  rtt?: number;
  /** Whether connection is metered/expensive */
  saveData?: boolean;
  /** Whether network quality is good enough for client processing */
  isGoodEnough: boolean;
  /** Warning message if network is poor */
  warningMessage?: string;
}

/**
 * Get network information using the Network Information API.
 * Falls back to conservative assumptions if API not available.
 */
export function getNetworkInfo(): NetworkInfo {
  // Check if Network Information API is available
  const connection =
    (navigator as any).connection ||
    (navigator as any).mozConnection ||
    (navigator as any).webkitConnection;

  if (!connection) {
    // API not available - assume good network
    console.log(
      "Network Information API not available, assuming good connection"
    );
    return {
      effectiveType: "unknown",
      isGoodEnough: true,
    };
  }

  const effectiveType = connection.effectiveType || "4g";
  const downlink = connection.downlink; // Mbps
  const rtt = connection.rtt; // ms
  const saveData = connection.saveData || false;

  // Determine if network is good enough
  const isGoodEnough = checkIfNetworkIsGoodEnough(
    effectiveType,
    downlink,
    rtt,
    saveData
  );

  // Generate warning message if network is poor
  let warningMessage: string | undefined;
  if (!isGoodEnough) {
    if (saveData) {
      warningMessage =
        "Data saver mode is enabled. Using server processing to save bandwidth.";
    } else if (effectiveType === "slow-2g" || effectiveType === "2g") {
      warningMessage = `Slow network detected (${effectiveType}). Model download may take several minutes.`;
    } else if (downlink && downlink < 1) {
      warningMessage = `Slow connection (${downlink.toFixed(
        1
      )} Mbps). Consider using server processing.`;
    } else if (rtt && rtt > 500) {
      warningMessage = `High latency (${rtt}ms). Network may be unstable.`;
    }
  }

  return {
    effectiveType,
    downlink,
    rtt,
    saveData,
    isGoodEnough,
    warningMessage,
  };
}

/**
 * Check if network quality is sufficient for client-side processing.
 *
 * Criteria:
 * - Not on slow-2g or 2g
 * - Downlink > 1 Mbps (if available)
 * - RTT < 500ms (if available)
 * - Data saver mode not enabled
 */
function checkIfNetworkIsGoodEnough(
  effectiveType: string,
  downlink?: number,
  rtt?: number,
  saveData?: boolean
): boolean {
  // Data saver mode = don't download model
  if (saveData) {
    console.log("Data saver mode enabled, recommending server processing");
    return false;
  }

  // Very slow connections = don't download model
  if (effectiveType === "slow-2g" || effectiveType === "2g") {
    console.log(
      `Network too slow (${effectiveType}), recommending server processing`
    );
    return false;
  }

  // Check downlink speed if available
  if (downlink !== undefined && downlink < 1) {
    console.log(
      `Downlink too slow (${downlink} Mbps), recommending server processing`
    );
    return false;
  }

  // Check RTT if available (high latency = unstable connection)
  if (rtt !== undefined && rtt > 500) {
    console.log(`RTT too high (${rtt}ms), network may be unstable`);
    return false;
  }

  return true;
}

/**
 * Should client-side processing be used based on network quality?
 * More conservative check than isGoodEnough - only enables on clearly good networks.
 */
export function shouldUseClientProcessing(): boolean {
  const network = getNetworkInfo();

  // If we can't check, assume it's okay (API not available)
  if (network.effectiveType === "unknown") {
    return true;
  }

  // Only use client processing on good networks
  return (
    network.isGoodEnough &&
    network.effectiveType !== "3g" && // Be conservative with 3g
    !network.saveData
  );
}

/**
 * Estimate model download time based on network speed.
 * @param modelSizeMB - Size of model in megabytes
 * @returns Estimated download time in seconds, or null if can't estimate
 */
export function estimateDownloadTime(modelSizeMB: number): number | null {
  const network = getNetworkInfo();

  if (!network.downlink) {
    return null; // Can't estimate without downlink speed
  }

  // Convert Mbps to MBps (divide by 8)
  const downloadSpeedMBps = network.downlink / 8;

  // Calculate time in seconds
  const timeSeconds = modelSizeMB / downloadSpeedMBps;

  // Add 20% buffer for overhead
  return timeSeconds * 1.2;
}

/**
 * Get user-friendly message about network quality and download time.
 * @param modelSizeMB - Size of model in megabytes
 */
export function getNetworkMessage(modelSizeMB: number = 250): string {
  const network = getNetworkInfo();

  if (network.warningMessage) {
    return network.warningMessage;
  }

  const downloadTime = estimateDownloadTime(modelSizeMB);

  if (downloadTime !== null) {
    if (downloadTime < 10) {
      return `Model will download in ~${Math.ceil(
        downloadTime
      )} seconds on your current connection.`;
    } else if (downloadTime < 60) {
      return `Model will download in ~${Math.ceil(
        downloadTime
      )} seconds. This may take a moment.`;
    } else {
      const minutes = Math.ceil(downloadTime / 60);
      return `Model download will take ~${minutes} minute${
        minutes > 1 ? "s" : ""
      }. Consider using server processing.`;
    }
  }

  return "Model will download on first use (stored for future sessions).";
}

/**
 * Monitor network changes and execute callback when network quality changes.
 * Returns cleanup function.
 */
export function watchNetworkChanges(
  callback: (network: NetworkInfo) => void
): () => void {
  const connection =
    (navigator as any).connection ||
    (navigator as any).mozConnection ||
    (navigator as any).webkitConnection;

  if (!connection) {
    // API not available, can't watch
    return () => {};
  }

  const handler = () => {
    callback(getNetworkInfo());
  };

  connection.addEventListener("change", handler);

  // Return cleanup function
  return () => {
    connection.removeEventListener("change", handler);
  };
}
