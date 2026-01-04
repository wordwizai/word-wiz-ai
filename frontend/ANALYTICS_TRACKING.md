# Vercel Analytics - Signup Button Tracking

This document describes the custom event tracking implementation for signup buttons across the Word Wiz AI website.

## Overview

All signup button clicks are tracked using Vercel Analytics custom events. Each click sends an event with contextual information about where and how the user initiated signup.

## Event Structure

**Event Name:** `signup_button_click`

**Parameters:**
- `location` (string): Where the signup button was clicked
- `method` (string): The signup method used ('google', 'email', or 'link')
- `context` (string): Additional context (page/article title, or 'none')

## Tracked Locations

### 1. Navbar (`navbar`)
- **File:** `frontend/src/components/LandingPageNavbar.tsx`
- **Method:** `link`
- **Context:** `none`
- **Button Text:** "Sign Up"
- **Description:** Primary navigation signup button visible on all landing pages

### 2. Hero Section (`hero`)
- **File:** `frontend/src/pages/LandingPage.tsx`
- **Methods:** `google`, `link`
- **Context:** `none`
- **Button Texts:** "Sign in with Google", "Create Account"
- **Description:** Main call-to-action buttons in the landing page hero section

### 3. Landing CTA Section (`landing_cta`)
- **File:** `frontend/src/components/LandingPageCTA.tsx`
- **Methods:** `google`, `link`
- **Context:** `none`
- **Button Texts:** "Sign in with Google", "Create Account"
- **Description:** Secondary CTA section on landing page

### 4. Article Final CTA (`article_final_cta`)
- **File:** `frontend/src/components/ArticlePageTemplate.tsx`
- **Method:** `link`
- **Context:** Article headline (e.g., "Why Does My Child Hate Reading?")
- **Button Text:** "Get Started Free"
- **Description:** Bottom CTA on article pages

### 5. Inline CTAs in Articles/Guides (`inline_cta`)
- **File:** `frontend/src/components/ArticlePageTemplate.tsx`
- **Method:** `link`
- **Context:** Article headline
- **Button Texts:** Varies (e.g., "Try Free", "Start Practicing")
- **Description:** CTAs embedded within article content

### 6. Comparison Pages (`comparison_product_card`, `comparison_final_cta`)
- **File:** `frontend/src/components/ComparisonPageTemplate.tsx`
- **Method:** `link`
- **Context:** Comparison page title
- **Button Texts:** "Sign Up Free", "Get Started Free"
- **Description:** CTAs on product comparison pages

### 7. Footer (`footer`)
- **File:** `frontend/src/components/LandingPageFooter.tsx`
- **Method:** `link`
- **Context:** `none`
- **Link Text:** "Sign Up"
- **Description:** Footer signup link

### 8. Signup Form (`signup_form`)
- **File:** `frontend/src/components/create-account-form.tsx`
- **Methods:** `google`, `email`
- **Context:** `none`
- **Button Texts:** Google icon button, "Create account" (form submit)
- **Description:** The actual signup form where users create accounts

## Implementation Details

### Central Utility Module
Located at: `frontend/src/utils/analytics.ts`

```typescript
import { track } from '@vercel/analytics';

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
```

### Usage Example

```typescript
import { trackSignupClick } from '@/utils/analytics';

// Track a navbar signup link click
<Link to="/signup">
  <Button onClick={() => trackSignupClick('navbar', 'link')}>
    Sign Up
  </Button>
</Link>

// Track Google signup with context
<Button onClick={() => {
  trackSignupClick('hero', 'google');
  googleLogin();
}}>
  Sign in with Google
</Button>
```

## Testing in Production

Once deployed to Vercel:

1. **Access Vercel Analytics Dashboard**
   - Go to your Vercel project dashboard
   - Navigate to Analytics → Events
   - Look for `signup_button_click` events

2. **Verify Event Data**
   Each event should include:
   - Event name: `signup_button_click`
   - Timestamp
   - Page URL where the event occurred
   - Custom parameters: `location`, `method`, `context`

3. **Test Different Scenarios**
   - Click signup buttons in different locations (navbar, hero, article)
   - Try both Google and email signup methods
   - Check that context is captured for article/guide pages

## Benefits

1. **Conversion Funnel Analysis**: Understand which signup buttons drive the most conversions
2. **A/B Testing**: Compare performance of different button placements
3. **User Journey Mapping**: Track how users navigate before signing up
4. **Content Effectiveness**: See which articles/guides lead to signups
5. **Method Preferences**: Understand if users prefer Google vs email signup

## Notes

- All tracking is non-blocking - if Vercel Analytics fails, signup functionality continues
- No personal information is tracked in these events
- Events are only sent from the production Vercel deployment
- The `@vercel/analytics` package is already installed and configured in the app
