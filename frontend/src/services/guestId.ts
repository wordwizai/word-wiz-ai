/**
 * The try page's anonymous visitor id (see backend/crud/guest_users.py).
 *
 * One random id per browser, sent with each try-mode reading. The backend
 * keeps one guest row per id, so a visitor who reads several sentences or
 * comes back later counts once. Sign-up sends the id along so that guest row
 * becomes the new account instead of a second row for the same person.
 *
 * Storage can be blocked (private windows, strict settings). Then the id
 * lasts for this page load only.
 */

const KEY = "wwai_guest_id";
let memoryId: string | null = null;

const newId = (): string =>
  crypto.randomUUID?.() ??
  Array.from(crypto.getRandomValues(new Uint8Array(16)), (b) =>
    b.toString(16).padStart(2, "0")
  ).join("");

/** This browser's guest id, if it has used try mode. Never creates one. */
export function peekGuestId(): string | null {
  try {
    return localStorage.getItem(KEY) ?? memoryId;
  } catch {
    return memoryId;
  }
}

/** This browser's guest id, creating it on first use. */
export function getGuestId(): string {
  const existing = peekGuestId();
  if (existing) return existing;
  memoryId = newId();
  try {
    localStorage.setItem(KEY, memoryId);
  } catch {
    // Kept in memory for this page load.
  }
  return memoryId;
}

/** Forget the id once it has become an account. */
export function clearGuestId(): void {
  memoryId = null;
  try {
    localStorage.removeItem(KEY);
  } catch {
    // Nothing stored.
  }
}
