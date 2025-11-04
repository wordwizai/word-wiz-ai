/**
 * Device capabilities detection for client-side phoneme processing.
 *
 * This module provides utilities to detect:
 * - Available RAM (estimate)
 * - Mobile vs desktop devices
 * - WebAssembly support
 * - Overall device capability for running AI models
 */

export interface DeviceCapabilities {
  /** Whether the device can run the AI model */
  canRunModel: boolean;
  /** Whether we should recommend disabling client processing */
  shouldRecommendDisabling: boolean;
  /** Estimated RAM in GB (may not be accurate on all browsers) */
  estimatedRAM: number;
  /** Whether the device is mobile */
  isMobile: boolean;
  /** Whether WebAssembly is supported */
  hasWebAssembly: boolean;
  /** Device memory warning message if applicable */
  warningMessage?: string;
}

/**
 * Estimate available device RAM.
 * Note: This uses the Device Memory API which is not supported on all browsers.
 * Falls back to 4GB assumption if not available.
 */
export function estimateRAM(): number {
  // Device Memory API (Chrome, Edge)
  if ("deviceMemory" in navigator) {
    return (navigator as any).deviceMemory as number;
  }

  // Fallback: assume 4GB for desktop, 2GB for mobile
  if (isMobileDevice()) {
    return 2;
  }

  return 4; // Conservative estimate
}

/**
 * Check if the device is mobile.
 * Checks both user agent and various device characteristics.
 */
export function isMobileDevice(): boolean {
  // User agent check
  const userAgent = navigator.userAgent.toLowerCase();
  const mobileRegex =
    /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini|mobile|tablet/i;
  const isMobileUA = mobileRegex.test(userAgent);

  // Additional checks for tablets masquerading as desktop
  const hasTouch = "ontouchstart" in window || navigator.maxTouchPoints > 0;
  const isSmallScreen =
    window.screen.width <= 768 || window.screen.height <= 768;

  return isMobileUA || (hasTouch && isSmallScreen);
}

/**
 * Check if WebAssembly is supported.
 */
export function hasWebAssemblySupport(): boolean {
  try {
    if (
      typeof WebAssembly === "object" &&
      typeof WebAssembly.instantiate === "function"
    ) {
      // Test instantiation with a minimal module
      const module = new WebAssembly.Module(
        Uint8Array.of(0x0, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00)
      );
      if (module instanceof WebAssembly.Module) {
        return true;
      }
    }
  } catch (e) {
    // WebAssembly not supported or failed to instantiate
  }
  return false;
}

/**
 * Check overall device capabilities for running client-side AI models.
 *
 * Criteria for running models:
 * - WebAssembly support (required)
 * - At least 4GB RAM for desktop, 3GB for mobile (recommended)
 * - Not a very old mobile device
 *
 * @returns Device capabilities assessment
 */
export function checkDeviceCapabilities(): DeviceCapabilities {
  const hasWasm = hasWebAssemblySupport();
  const isMobile = isMobileDevice();
  const memory = estimateRAM();

  // Minimum RAM requirements - VERY permissive to allow mobile devices to try
  // Models are ~325MB total, modern phones can handle this even with 2GB
  const minRAMDesktop = 2; // 2GB for desktop (very low bar)
  const minRAMMobile = 1; // 1GB for mobile (let them try, will fallback if fails)
  const minRAM = isMobile ? minRAMMobile : minRAMDesktop;

  const hasEnoughRAM = memory >= minRAM;

  // Determine if device can run the model
  const canRunModel = hasWasm && hasEnoughRAM;

  // Should we recommend disabling?
  // Recommend disabling if:
  // - No WebAssembly support (hard requirement)
  // Very permissive - let devices try even if low RAM
  const shouldRecommendDisabling = !hasWasm;

  // Generate warning message
  let warningMessage: string | undefined;
  if (!hasWasm) {
    warningMessage =
      "Your browser does not support WebAssembly. Client-side processing is unavailable.";
  } else if (!hasEnoughRAM) {
    warningMessage = `Your device has ${memory}GB RAM. At least ${minRAM}GB is recommended for smooth performance.`;
  } else if (isMobile && memory < 4) {
    warningMessage =
      "Mobile devices may experience slower performance. Consider using server processing for better experience.";
  }

  return {
    canRunModel,
    shouldRecommendDisabling,
    estimatedRAM: memory,
    isMobile,
    hasWebAssembly: hasWasm,
    warningMessage,
  };
}

/**
 * Get a user-friendly message about device capabilities.
 */
export function getDeviceCapabilityMessage(
  capabilities: DeviceCapabilities
): string {
  if (capabilities.warningMessage) {
    return capabilities.warningMessage;
  }

  if (capabilities.canRunModel) {
    return "Your device supports client-side processing for faster results.";
  }

  return "Server-side processing will be used for your device.";
}

/**
 * Check if device should auto-enable client processing.
 * More conservative than canRunModel - only enables on clearly capable devices.
 */
export function shouldAutoEnableClientProcessing(): boolean {
  const capabilities = checkDeviceCapabilities();

  // Auto-enable only if:
  // - Device can run model
  // - Not recommended to disable
  // - Has at least 4GB RAM (or 3GB if desktop)
  return (
    capabilities.canRunModel &&
    !capabilities.shouldRecommendDisabling &&
    capabilities.estimatedRAM >= (capabilities.isMobile ? 4 : 3)
  );
}
