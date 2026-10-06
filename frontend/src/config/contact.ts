export const SUPPORT_EMAIL = "contactwordwizai@gmail.com";

/** mailto: link to support with the subject (and optional body) filled in. */
export function supportMailto(subject: string, body?: string): string {
  let href = `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(subject)}`;
  if (body) href += `&body=${encodeURIComponent(body)}`;
  return href;
}
