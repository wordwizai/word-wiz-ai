/**
 * Guest ("try it") audio analysis: no account, no session.
 *
 * Posts one recording to the backend's public /guest/analyze-audio route and
 * streams back the same events signed-in practice gets (analysis, feedback,
 * audio_feedback_file), followed by "complete". The backend only accepts
 * sentences from the practice-word pages and rate-limits each visitor. With
 * a guestId, the backend counts the browser as one anonymous guest user
 * (services/guestId.ts).
 */

import { API_URL } from "@/api";
import { readSSEStream, type AudioAnalysisEvent } from "@/services/audioTransport";

export class GuestAnalysisError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const FALLBACK_MESSAGE =
  "We couldn't check that reading. Please try again in a moment.";

// Shown when the route isn't there, e.g. the frontend shipped before the
// backend that serves it.
const UNAVAILABLE_MESSAGE =
  "Trying without an account isn't available right now. You can still create a free account to practice.";

async function errorMessage(response: Response): Promise<string> {
  if (response.status === 404) return UNAVAILABLE_MESSAGE;
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    // Not JSON; fall through.
  }
  return FALLBACK_MESSAGE;
}

export async function analyzeGuestAudio(
  file: File,
  sentence: string,
  onEvent: (event: AudioAnalysisEvent) => void,
  signal?: AbortSignal,
  guestId?: string
): Promise<void> {
  const formData = new FormData();
  formData.append("audio_file", file);
  formData.append("attempted_sentence", sentence);
  if (guestId) formData.append("guest_id", guestId);

  let response: Response;
  try {
    response = await fetch(`${API_URL}/guest/analyze-audio`, {
      method: "POST",
      body: formData,
      signal,
    });
  } catch (err) {
    if ((err as Error)?.name === "AbortError") throw err;
    throw new GuestAnalysisError(
      "We couldn't reach Word Wiz. Check your internet connection and try again.",
      0
    );
  }

  if (!response.ok) {
    throw new GuestAnalysisError(await errorMessage(response), response.status);
  }

  await readSSEStream(response, onEvent);
}
