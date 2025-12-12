# Error Viewer for Practice Page Implementation Guide

**Version:** 1.0  
**Created:** December 2024  
**Status:** 🚧 In Progress

---

## Table of Contents

1. [Overview](#overview)
2. [Current State Analysis](#current-state-analysis)
3. [Requirements](#requirements)
4. [Implementation Phases](#implementation-phases)
5. [Technical Design](#technical-design)
6. [Quality Assurance](#quality-assurance)
7. [References](#references)

---

## Overview

This guide outlines the implementation of a user-friendly error notification system for the practice page. The system will replace console.log error messages with toast notifications that provide clear, actionable feedback to users when errors occur during audio processing, streaming, or other practice activities.

### Key Objectives

- **User-Friendly Error Display**: Show errors as toast notifications instead of silent console logging
- **Centralized Error Handling**: Create a unified system for all stream and processing errors
- **Clear Error Messages**: Provide helpful, actionable error messages to users
- **Non-Intrusive**: Use toast notifications that don't block the user experience
- **Consistent Design**: Match the existing UI/UX patterns of the application

### Core Principles

- **80/20 Rule**: Focus on the most common error scenarios that affect users
- **No Overengineering**: Use a simple, proven toast library (sonner) already popular in the React ecosystem
- **Gradual Enhancement**: Build on existing error handling without breaking current functionality
- **User-Centric**: Error messages should be clear, helpful, and actionable
- **Maintain Performance**: Error handling should not impact app performance

---

## Current State Analysis

### Existing Error Handling

1. **BasePractice.tsx** (Lines 108-111)
   - Current: `console.error("Stream error:", err);`
   - Issue: Users see no feedback when stream errors occur
   - Location: `onError` callback in useHybridAudioAnalysis hook

2. **ChoiceStoryBasePractice.tsx** (Lines 85-87)
   - Current: `console.error("Stream error:", err);`
   - Issue: Same as BasePractice, no user-facing error notification
   - Location: `onError` callback in useHybridAudioAnalysis hook

3. **useAudioAnalysisStream.ts** (Lines 38-40, 132, 140-143)
   - Current: `options?.onError?.("Not authenticated");`
   - Issue: Error passed to callback but not displayed to user
   - Locations: Authentication check, SSE parsing errors, fetch catch block

4. **useAudioTransport.ts** (Lines 71-75, 99-102, 114)
   - Current: `opts.onError?.(event.data);`
   - Issue: Error event received but not displayed to user
   - Locations: Error event handling, transport errors, connection failures

5. **useHybridAudioAnalysis.ts** (Lines 131-146, 239-261)
   - Current: `console.error` and `console.warn` for model and extraction failures
   - Issue: Users unaware when client-side processing fails
   - Locations: Model loading failures, extraction failures

6. **GenericPractice.tsx** (Line 103)
   - Current: `alert("Failed to play audio feedback. Please check your device volume and try again.");`
   - Issue: Uses native alert which is intrusive and doesn't match UI
   - Location: Audio playback error in BasePractice

### Existing Strengths

- ✅ Errors are already being caught and logged
- ✅ Error callbacks (`onError`) are already in place
- ✅ Error categorization is partially done (authentication, parsing, transport)
- ✅ UI components library (Radix UI) is already integrated

### Current Limitations

- ❌ No user-facing error notifications (except one intrusive alert)
- ❌ Users don't know when errors occur during practice
- ❌ Error messages are developer-focused, not user-friendly
- ❌ No consistent error display system
- ❌ Silent failures can confuse users
- ❌ Native alert() is used in one place (not consistent with UI)

---

## Requirements

### Functional Requirements

1. **Toast Notification System**
   - Display errors as toast notifications (non-blocking overlay)
   - Support different error types (error, warning, info)
   - Auto-dismiss after configurable duration (default: 5 seconds)
   - Allow manual dismiss with close button
   - Stack multiple toasts if needed
   - Accessible (screen reader support)

2. **Error Categorization**
   - Network/Connection errors
   - Authentication errors
   - Audio processing errors
   - Model loading errors
   - Audio playback errors
   - Stream parsing errors
   - Unknown/unexpected errors

3. **User-Friendly Messages**
   - Clear, non-technical language
   - Actionable suggestions when possible
   - Appropriate tone (helpful, not alarming)
   - Context-aware (what operation failed)

4. **Integration Points**
   - All existing `onError` callbacks should trigger toasts
   - All `console.error` calls related to user-facing errors should trigger toasts
   - Maintain backward compatibility with existing error handling

### Non-Functional Requirements

1. **Performance**: Toast rendering should not impact practice page performance
2. **Accessibility**: Toasts must be screen-reader friendly (ARIA live regions)
3. **Mobile**: Toasts should work well on mobile devices with appropriate sizing
4. **Consistency**: Match existing UI design patterns (colors, fonts, animations)

---

## Implementation Phases

### Phase 1: Foundation and Planning ✅

**Goal**: Understand current implementation and create detailed plan

#### Todos

- [x] Analyze existing error handling in all practice components
- [x] Review hooks for error callbacks (useHybridAudioAnalysis, useAudioTransport, etc.)
- [x] Identify all error scenarios and locations
- [x] Research toast libraries (sonner recommended)
- [x] Create implementation guide document

#### QA Checklist

- [x] All error locations documented
- [x] Implementation guide complete and reviewed
- [x] Technical approach validated

---

### Phase 2: Toast System Setup ✅

**Goal**: Install and configure toast notification library

#### Todos

- [x] **Install sonner library**
  - Run: `cd frontend && npm install sonner`
  - Verify installation in package.json

- [x] **Create Toaster component** (`frontend/src/components/ui/toaster.tsx`)
  - Import Toaster from sonner
  - Configure default settings (position, duration)
  - Style to match application theme
  - Export for use in App

- [x] **Add Toaster to application root** (`frontend/src/App.tsx` or main component)
  - Import Toaster component
  - Place in root of component tree (after other providers)
  - Verify toasts can be triggered from anywhere in app

- [x] **Test basic toast functionality**
  - Build verified successfully
  - Ready for integration testing

#### Implementation Details

**File: `frontend/src/components/ui/toaster.tsx`**

```tsx
import { Toaster as Sonner } from "sonner";

export function Toaster() {
  return (
    <Sonner
      position="top-center"
      toastOptions={{
        duration: 5000,
        classNames: {
          toast: "bg-card text-card-foreground border-border",
          title: "text-foreground",
          description: "text-muted-foreground",
          error: "bg-destructive text-destructive-foreground",
        },
      }}
    />
  );
}
```

**File: `frontend/src/App.tsx` (or main.tsx)**

```tsx
import { Toaster } from "@/components/ui/toaster";

function App() {
  return (
    <>
      {/* Existing app structure */}
      <Toaster />
    </>
  );
}
```

#### QA Checklist

- [x] sonner installed successfully
- [x] Toaster component created and styled
- [x] Toaster added to app root
- [x] Build succeeds with toast system
- [ ] Test toast displays correctly (will test during integration)
- [ ] Toast auto-dismisses after 5 seconds (will test during integration)
- [ ] Toast can be manually dismissed (will test during integration)
- [ ] Styling matches app theme (will verify during integration)
- [ ] Works on mobile devices (will test during integration)

---

### Phase 3: Error Handling Utilities ✅

**Goal**: Create reusable utilities for error categorization and toast display

#### Todos

- [x] **Create error utility module** (`frontend/src/utils/errorHandling.ts`)
  - Error categorization function
  - User-friendly message mapping
  - Toast helper functions

- [x] **Define error categories and messages**
  - Network/connection errors
  - Authentication errors
  - Audio processing errors
  - Model loading errors
  - Playback errors
  - Fallback for unknown errors

- [x] **Create showErrorToast helper function**
  - Accept error object or string
  - Categorize error
  - Map to user-friendly message
  - Trigger appropriate toast (error, warning, info)
  - Include actionable suggestions when applicable

- [x] **Create specialized toast helpers**
  - `showNetworkError()` - for connection issues
  - `showAudioError()` - for audio processing issues
  - `showAuthError()` - for authentication issues
  - `showModelError()` - for model loading issues

#### Implementation Details

**File: `frontend/src/utils/errorHandling.ts`**

```typescript
import { toast } from "sonner";

export enum ErrorCategory {
  NETWORK = "network",
  AUTHENTICATION = "authentication",
  AUDIO_PROCESSING = "audio_processing",
  MODEL_LOADING = "model_loading",
  AUDIO_PLAYBACK = "audio_playback",
  STREAM_PARSING = "stream_parsing",
  UNKNOWN = "unknown",
}

interface ErrorMessage {
  title: string;
  description: string;
  action?: string;
}

const ERROR_MESSAGES: Record<ErrorCategory, ErrorMessage> = {
  [ErrorCategory.NETWORK]: {
    title: "Connection Error",
    description: "Unable to connect to the server. Please check your internet connection.",
    action: "Try again in a moment",
  },
  [ErrorCategory.AUTHENTICATION]: {
    title: "Authentication Required",
    description: "You need to be logged in to use this feature.",
    action: "Please sign in again",
  },
  [ErrorCategory.AUDIO_PROCESSING]: {
    title: "Audio Processing Failed",
    description: "We couldn't analyze your recording. Please try recording again.",
    action: "Check your microphone and try again",
  },
  [ErrorCategory.MODEL_LOADING]: {
    title: "Loading Failed",
    description: "Failed to load speech recognition models.",
    action: "Refresh the page to try again",
  },
  [ErrorCategory.AUDIO_PLAYBACK]: {
    title: "Playback Error",
    description: "Unable to play audio feedback.",
    action: "Check your device volume and try again",
  },
  [ErrorCategory.STREAM_PARSING]: {
    title: "Processing Error",
    description: "An error occurred while processing your request.",
    action: "Please try again",
  },
  [ErrorCategory.UNKNOWN]: {
    title: "Something Went Wrong",
    description: "An unexpected error occurred.",
    action: "Please try again",
  },
};

/**
 * Categorize error based on error message or type
 */
export function categorizeError(error: string | Error): ErrorCategory {
  const message = typeof error === "string" ? error : error.message;
  const lowerMessage = message.toLowerCase();

  if (lowerMessage.includes("not authenticated") || lowerMessage.includes("authentication")) {
    return ErrorCategory.AUTHENTICATION;
  }
  if (lowerMessage.includes("network") || lowerMessage.includes("connect") || lowerMessage.includes("timeout")) {
    return ErrorCategory.NETWORK;
  }
  if (lowerMessage.includes("audio") && lowerMessage.includes("play")) {
    return ErrorCategory.AUDIO_PLAYBACK;
  }
  if (lowerMessage.includes("model") || lowerMessage.includes("load")) {
    return ErrorCategory.MODEL_LOADING;
  }
  if (lowerMessage.includes("parse") || lowerMessage.includes("sse")) {
    return ErrorCategory.STREAM_PARSING;
  }
  if (lowerMessage.includes("audio") || lowerMessage.includes("recording")) {
    return ErrorCategory.AUDIO_PROCESSING;
  }

  return ErrorCategory.UNKNOWN;
}

/**
 * Display error toast with user-friendly message
 */
export function showErrorToast(error: string | Error, category?: ErrorCategory) {
  const errorCategory = category || categorizeError(error);
  const errorMessage = ERROR_MESSAGES[errorCategory];

  toast.error(errorMessage.title, {
    description: `${errorMessage.description} ${errorMessage.action ? `\n\n${errorMessage.action}` : ""}`,
  });

  // Log detailed error for debugging
  console.error(`[${errorCategory}]`, error);
}

/**
 * Specialized toast helpers
 */
export function showNetworkError(error?: string | Error) {
  showErrorToast(error || "Network error", ErrorCategory.NETWORK);
}

export function showAudioError(error?: string | Error) {
  showErrorToast(error || "Audio processing error", ErrorCategory.AUDIO_PROCESSING);
}

export function showAuthError(error?: string | Error) {
  showErrorToast(error || "Authentication error", ErrorCategory.AUTHENTICATION);
}

export function showModelError(error?: string | Error) {
  showErrorToast(error || "Model loading error", ErrorCategory.MODEL_LOADING);
}

export function showAudioPlaybackError(error?: string | Error) {
  showErrorToast(error || "Audio playback error", ErrorCategory.AUDIO_PLAYBACK);
}

/**
 * Show info toast (for non-error notifications)
 */
export function showInfoToast(title: string, description?: string) {
  toast.info(title, { description });
}

/**
 * Show success toast
 */
export function showSuccessToast(title: string, description?: string) {
  toast.success(title, { description });
}
```

#### QA Checklist

- [x] Error utility module created
- [x] All error categories defined
- [x] User-friendly messages written
- [x] Error categorization logic implemented
- [x] Toast helpers created
- [ ] Error categorization tested (will test during integration)
- [ ] Error messages verified as clear and helpful (will verify during integration)
- [ ] Actions/suggestions verified (will verify during integration)
- [x] Developer logging maintained for debugging

---

### Phase 4: Integration with Practice Components

**Goal**: Replace all error console.logs and alerts with toast notifications

#### Todos

- [ ] **Update BasePractice.tsx**
  - Replace console.error in onError with showErrorToast
  - Replace alert() in audio playback with showAudioPlaybackError
  - Import error utility functions
  - Test error scenarios

- [ ] **Update ChoiceStoryBasePractice.tsx**
  - Replace console.error in onError with showErrorToast
  - Import error utility functions
  - Test error scenarios

- [ ] **Update useHybridAudioAnalysis.ts**
  - Add showModelError for model loading failures
  - Add showAudioError for extraction failures
  - Keep console.error for debugging but add toast for user feedback
  - Test model loading and extraction errors

- [ ] **Update useAudioAnalysisStream.ts**
  - Add showAuthError for authentication errors
  - Add showErrorToast for parsing errors
  - Add showNetworkError for fetch errors
  - Keep existing onError callback behavior for backward compatibility

- [ ] **Update useAudioTransport.ts**
  - Add showErrorToast for transport errors
  - Add showNetworkError for connection errors
  - Maintain callback chain for component-level error handling

#### Implementation Details

**File: `frontend/src/components/practice/BasePractice.tsx`**

```typescript
// Add import
import { showErrorToast, showAudioPlaybackError } from "@/utils/errorHandling";

// Replace onError callback (line 108)
onError: (err) => {
  console.error("Stream error:", err);
  showErrorToast(err);  // Add this line
  setIsProcessing(false);
},

// Replace audio playback error (line 100-106)
audio.play().catch((error) => {
  console.error("[AudioFeedback] Failed to play audio:", error);
  showAudioPlaybackError(error);  // Replace alert() with this
});
```

**File: `frontend/src/components/practice/ChoiceStoryBasePractice.tsx`**

```typescript
// Add import
import { showErrorToast } from "@/utils/errorHandling";

// Replace onError callback (line 85)
onError: (err) => {
  console.error("Stream error:", err);
  showErrorToast(err);  // Add this line
  setIsProcessing(false);
},
```

**File: `frontend/src/hooks/useHybridAudioAnalysis.ts`**

```typescript
// Add import
import { showModelError, showAudioError } from "@/utils/errorHandling";

// In initializeModels function (around line 141-144)
} else {
  console.error("[HybridAudioAnalysis] ❌ Both models failed to load");
  showModelError("Failed to load speech recognition models");  // Add this
  throw new Error("Failed to load both models");
}

// In processAudio function (around line 239-247)
} else {
  console.error(
    `[HybridAudioAnalysis] ❌ Both extractions failed after retries`
  );
  if (phonemeResult.status === "rejected") {
    console.error("Phoneme error:", phonemeResult.reason);
  }
  if (wordResult.status === "rejected") {
    console.error("Word error:", wordResult.reason);
  }
  // Don't show toast here - it's a fallback scenario, not a failure
  // Backend will handle the processing
}

// In processAudio catch block (around line 262-267)
} catch (error) {
  console.error(
    "[HybridAudioAnalysis] Unexpected error during extraction:",
    error
  );
  showAudioError(error as Error);  // Add this
  performanceTracker.recordClientExtraction(0, false);
}
```

**File: `frontend/src/hooks/useAudioAnalysisStream.ts`**

```typescript
// Add import
import { showAuthError, showErrorToast, showNetworkError } from "@/utils/errorHandling";

// In start function (line 38)
if (!token) {
  showAuthError("Not authenticated");  // Add this
  options?.onError?.("Not authenticated");
  return;
}

// In parse error catch (line 132)
} catch (err) {
  showErrorToast("Failed to parse server response");  // Add this
  options?.onError?.("Failed to parse SSE message");
}

// In fetch catch (line 140)
.catch((err) => {
  showNetworkError(err.message);  // Add this
  options?.onError?.(err.message);
  options?.onProcessingEnd?.();
});
```

**File: `frontend/src/hooks/useAudioTransport.ts`**

```typescript
// Add import
import { showErrorToast, showNetworkError } from "@/utils/errorHandling";

// In handleEvent function (line 71)
case "error":
  setIsProcessing(false);
  opts.onProcessingEnd?.();
  showErrorToast(event.data);  // Add this
  opts.onError?.(event.data);
  break;

// In transport error callback (line 99)
onError: (error) => {
  console.error("Transport error:", error);
  showErrorToast(error);  // Add this
  optionsRef.current.onError?.(error);
},

// In connect catch (line 114)
.catch((err) => {
  console.error("Failed to initialize transport:", err);
  showNetworkError(err);  // Add this
  optionsRef.current.onError?.("Failed to connect. Please try again.");
});
```

#### QA Checklist

- [ ] All console.error calls replaced/supplemented with toasts
- [ ] Alert() removed and replaced with toast
- [ ] Error utility functions imported correctly
- [ ] Backward compatibility maintained (onError callbacks still work)
- [ ] Network errors show network toast
- [ ] Auth errors show auth toast
- [ ] Audio errors show audio toast
- [ ] Model errors show model toast
- [ ] All error scenarios tested
- [ ] Toast messages are user-friendly
- [ ] Developer console.error kept for debugging

---

### Phase 5: Testing and Quality Assurance

**Goal**: Comprehensive testing of all error scenarios and polish

#### Todos

- [ ] **Test network errors**
  - Disconnect internet and try to record
  - Verify network error toast appears
  - Check message is helpful

- [ ] **Test authentication errors**
  - Clear token and try to record
  - Verify auth error toast appears
  - Check message directs user to sign in

- [ ] **Test audio processing errors**
  - Send invalid audio file
  - Verify processing error toast appears
  - Check suggestions are helpful

- [ ] **Test model loading errors**
  - Block model loading (if possible)
  - Verify model error toast appears
  - Check message suggests refresh

- [ ] **Test audio playback errors**
  - Force audio playback failure (if possible)
  - Verify playback error toast appears
  - Check no alert() appears

- [ ] **Test mobile responsiveness**
  - View on mobile device or emulator
  - Verify toasts display correctly
  - Check sizing and positioning
  - Verify touch interactions work

- [ ] **Test multiple errors**
  - Trigger multiple errors in sequence
  - Verify toasts stack properly
  - Check auto-dismiss works
  - Verify manual dismiss works

- [ ] **Test accessibility**
  - Use screen reader
  - Verify toasts are announced
  - Check keyboard navigation
  - Verify ARIA attributes

- [ ] **Performance testing**
  - Verify no performance impact
  - Check memory usage
  - Test with rapid error triggering

- [ ] **Cross-browser testing**
  - Test in Chrome, Firefox, Safari
  - Verify consistent behavior
  - Check styling across browsers

#### QA Checklist

- [ ] All error scenarios trigger appropriate toasts
- [ ] Error messages are clear and helpful
- [ ] No more alert() dialogs
- [ ] No silent errors (all displayed to user)
- [ ] Toast auto-dismiss works (5 seconds)
- [ ] Manual dismiss works
- [ ] Multiple toasts stack correctly
- [ ] Mobile display is good
- [ ] Accessibility requirements met
- [ ] Performance is not impacted
- [ ] Works in all major browsers
- [ ] Developer logging still works
- [ ] Existing functionality not broken
- [ ] UI matches app design system

---

## Technical Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      App Root                           │
│                   <Toaster />                           │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ toast() calls
                            │
┌───────────────────────────┴─────────────────────────────┐
│            Error Handling Utilities                      │
│         (errorHandling.ts)                              │
│  - showErrorToast()                                     │
│  - showNetworkError()                                   │
│  - showAudioError()                                     │
│  - showAuthError()                                      │
│  - showModelError()                                     │
└───────────────────────────┬─────────────────────────────┘
                            ▲
                            │ imports
                            │
┌───────────────────────────┴─────────────────────────────┐
│              Practice Components & Hooks                 │
│                                                          │
│  BasePractice.tsx → showErrorToast()                    │
│  ChoiceStoryBasePractice.tsx → showErrorToast()        │
│  useHybridAudioAnalysis.ts → showModelError()          │
│  useAudioAnalysisStream.ts → showAuthError()           │
│  useAudioTransport.ts → showErrorToast()               │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Error Occurs**: Network failure, auth error, processing error, etc.
2. **Error Caught**: Try-catch block or error callback receives error
3. **Error Categorized**: `categorizeError()` determines error type
4. **Message Mapped**: Error category mapped to user-friendly message
5. **Toast Displayed**: `toast.error()` called with title and description
6. **Developer Log**: `console.error()` called for debugging
7. **Auto-Dismiss**: Toast auto-dismisses after 5 seconds (or manual dismiss)

### Component Responsibilities

**Toaster Component** (`toaster.tsx`)
- Render toast notifications
- Handle positioning and styling
- Manage toast lifecycle (auto-dismiss)
- Provide accessibility attributes

**Error Utilities** (`errorHandling.ts`)
- Categorize errors
- Map to user-friendly messages
- Provide helper functions
- Maintain developer logging

**Practice Components** (`BasePractice.tsx`, etc.)
- Catch errors in appropriate locations
- Call error utility functions
- Maintain existing functionality
- Don't implement error display logic

### Technology Choices

**Toast Library: sonner**
- ✅ Lightweight and performant
- ✅ Beautiful default styling
- ✅ Excellent TypeScript support
- ✅ Accessible out of the box
- ✅ Easy to customize
- ✅ Popular in React ecosystem

**Alternative Considered:**
- react-hot-toast: Good but sonner is more modern and lighter
- Custom solution: Overengineering for this use case

---

## Quality Assurance

### Comprehensive QA Checklist

#### Functionality
- [ ] All error scenarios trigger toasts
- [ ] Error messages are clear and actionable
- [ ] Toasts auto-dismiss after 5 seconds
- [ ] Manual dismiss works (close button)
- [ ] Multiple errors stack appropriately
- [ ] No duplicate toasts for same error
- [ ] Existing error callbacks still work
- [ ] No functionality broken

#### User Experience
- [ ] Error messages use plain language
- [ ] Messages include actionable suggestions
- [ ] Tone is helpful, not alarming
- [ ] No technical jargon
- [ ] Context is clear (what operation failed)
- [ ] Native alert() completely removed
- [ ] Toasts don't block user interaction

#### Design & Styling
- [ ] Toast styling matches app theme
- [ ] Colors are consistent (error = destructive)
- [ ] Typography matches app fonts
- [ ] Animations are smooth
- [ ] Positioning is appropriate (top-center)
- [ ] Visual hierarchy is clear

#### Mobile & Responsive
- [ ] Toasts display correctly on mobile
- [ ] Touch interactions work
- [ ] Sizing appropriate for small screens
- [ ] Text is readable on all devices
- [ ] No overflow or layout issues
- [ ] Works in portrait and landscape

#### Accessibility
- [ ] Toasts announced by screen readers
- [ ] ARIA live regions implemented
- [ ] Keyboard navigation works
- [ ] Focus management is correct
- [ ] Color contrast meets WCAG standards
- [ ] Text is resizable without breaking layout

#### Performance
- [ ] No performance degradation
- [ ] Memory usage is reasonable
- [ ] Rapid errors don't cause issues
- [ ] Toast rendering is smooth
- [ ] No unnecessary re-renders

#### Browser Compatibility
- [ ] Works in Chrome
- [ ] Works in Firefox
- [ ] Works in Safari
- [ ] Works in Edge
- [ ] Consistent behavior across browsers

#### Developer Experience
- [ ] Error logging still works (console.error)
- [ ] Error details available for debugging
- [ ] Code is maintainable
- [ ] Documentation is clear
- [ ] Easy to add new error types

---

## References

### Related Files

**Frontend Components:**
- `frontend/src/components/practice/BasePractice.tsx` - Base practice component
- `frontend/src/components/practice/ChoiceStoryBasePractice.tsx` - Choice story practice
- `frontend/src/components/practice/GenericPractice.tsx` - Generic practice wrapper
- `frontend/src/components/ui/toaster.tsx` - Toast component (to be created)

**Frontend Hooks:**
- `frontend/src/hooks/useHybridAudioAnalysis.ts` - Audio analysis orchestration
- `frontend/src/hooks/useAudioAnalysisStream.ts` - SSE audio streaming
- `frontend/src/hooks/useAudioTransport.ts` - WebSocket/SSE transport abstraction

**Frontend Utilities:**
- `frontend/src/utils/errorHandling.ts` - Error utilities (to be created)

### Related Implementation Guides

- `CLASSES_PAGE_IMPROVEMENT_GUIDE.md` - Example of implementation guide format
- `UI_MODERNIZATION_GUIDE.md` - UI design patterns and styling

### External Documentation

- [Sonner Documentation](https://sonner.emilkowal.ski/) - Toast library docs
- [Radix UI](https://www.radix-ui.com/) - Base UI component library
- [shadcn/ui](https://ui.shadcn.com/) - Component patterns used in app

---

## Success Metrics

After implementation, success can be measured by:

1. **User Awareness**: Users see clear feedback when errors occur (no more silent failures)
2. **Error Recovery**: Users can take action based on error messages
3. **Code Quality**: Error handling is centralized and maintainable
4. **Consistency**: All errors use the same display mechanism (toasts)
5. **UX Improvement**: No more intrusive alert() dialogs

---

## Future Enhancements (Out of Scope)

Following the 80/20 rule, these are intentionally excluded but could be considered later:

- Error analytics/tracking (e.g., Sentry integration)
- Retry mechanisms with progress feedback
- Error history/log viewer for users
- Customizable error message preferences
- Rich error details (expandable sections)
- Error reporting to developers
- Offline error queuing
- I18n/localization of error messages

---

## Notes

- This implementation follows the 80/20 rule - focusing on common error scenarios
- Toast notifications are non-blocking and user-friendly
- Developer logging is maintained for debugging purposes
- Implementation is incremental - can be rolled out phase by phase
- Each phase is testable and shippable independently
- Backward compatibility is maintained throughout

---

**End of Implementation Guide**
