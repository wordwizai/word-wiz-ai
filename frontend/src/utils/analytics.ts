import { track } from '@vercel/analytics';

/**
 * Track signup button clicks across the website
 * @param location - Where the signup button was clicked (e.g., 'navbar', 'hero', 'cta', 'article', 'guide', 'footer')
 * @param method - The signup method used (e.g., 'google', 'email', 'link')
 * @param context - Additional context about the signup (e.g., page name, article title)
 */
export const trackSignupClick = (
  location: string,
  method: 'google' | 'email' | 'link',
  context?: string
) => {
  track('signup_button_click', {
    location,
    method,
    context: context || 'none',
  });
};

/**
 * Track the guest "try it" funnel, one event name per step so each shows up
 * separately in Vercel Analytics:
 * - try_link_click: a "try it" link on a guide or practice page was clicked
 * - try_attempt: a sentence was read on /try (one per recording sent)
 * - try_completed: every sentence on the page was read
 * @param pattern - The practice pattern slug (e.g. 'a-e-magic-e')
 * @param location - Where it happened (e.g. 'practice-words', 'article_final_cta', 'try_page')
 */
export const trackTryEvent = (
  event: 'try_link_click' | 'try_attempt' | 'try_completed',
  pattern: string,
  location: string
) => {
  track(event, { pattern, location });
};
