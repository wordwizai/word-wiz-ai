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
