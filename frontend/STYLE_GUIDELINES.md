# Phoneme Assistant App - Style Guidelines

## Overview
This document outlines the comprehensive styling system for the Phoneme Assistant App, focusing on a playful and pastel aesthetic using Tailwind CSS and shadcn/ui components.

## Color Palette

### Base Colors (CSS Variables)
The application uses a sophisticated color system defined in `src/index.css` with both light and dark mode support.

#### Light Mode (`:root`)
```css
--background: oklch(0.98 0.01 280)
--foreground: oklch(0.2 0.02 280)
--primary: oklch(0.55 0.18 280)        /* Darker Lavender */
--primary-foreground: oklch(0.98 0.01 280)
--secondary: oklch(0.96 0.02 280)
--secondary-foreground: oklch(0.2 0.02 280)
--muted: oklch(0.96 0.02 280)
--muted-foreground: oklch(0.45 0.02 280)
--accent: oklch(0.96 0.02 280)
--accent-foreground: oklch(0.2 0.02 280)
--border: oklch(0.9 0.02 280)
--input: oklch(0.96 0.02 280)
--ring: oklch(0.55 0.18 280)           /* Darker Lavender */
--sidebar: oklch(0.98 0.01 280)
--sidebar-foreground: oklch(0.2 0.02 280)
--sidebar-primary: oklch(0.55 0.18 280) /* Darker Lavender */
--sidebar-primary-foreground: oklch(0.98 0.01 280)
--sidebar-ring: oklch(0.55 0.18 280)   /* Darker Lavender */
```

#### Dark Mode (`.dark`)
```css
--background: oklch(0.1 0.01 280)
--foreground: oklch(0.9 0.02 280)
--primary: oklch(0.65 0.18 280)        /* Darker Lavender */
--primary-foreground: oklch(0.1 0.01 280)
--secondary: oklch(0.15 0.02 280)
--secondary-foreground: oklch(0.9 0.02 280)
--muted: oklch(0.15 0.02 280)
--muted-foreground: oklch(0.6 0.02 280)
--accent: oklch(0.15 0.02 280)
--accent-foreground: oklch(0.9 0.02 280)
--border: oklch(0.2 0.02 280)
--input: oklch(0.15 0.02 280)
--ring: oklch(0.65 0.18 280)           /* Darker Lavender */
--sidebar: oklch(0.1 0.01 280)
--sidebar-foreground: oklch(0.9 0.02 280)
--sidebar-primary: oklch(0.65 0.18 280) /* Darker Lavender */
--sidebar-primary-foreground: oklch(0.1 0.01 280)
--sidebar-ring: oklch(0.65 0.18 280)   /* Darker Lavender */
```

### Pastel Color Palette
```css
--color-pastel-blue: oklch(0.95 0.05 240)
--color-pastel-mint: oklch(0.95 0.05 160)
--color-pastel-peach: oklch(0.95 0.05 30)
--color-pastel-purple: oklch(0.95 0.05 280)
--color-pastel-pink: oklch(0.95 0.05 340)
--color-pastel-lavender: oklch(0.95 0.05 270)
--color-pastel-yellow: oklch(0.95 0.05 80)
--color-pastel-coral: oklch(0.95 0.05 20)
--color-pastel-teal: oklch(0.95 0.05 180)
```

## Typography & Layout

### Headers
- **Main Dashboard Title**: `text-4xl font-bold` with gradient text effect
- **Section Headers**: `text-xl font-bold` with appropriate color schemes
- **Card Titles**: `text-lg font-semibold` or `font-bold`

### Spacing System
- **Main Container**: `space-y-8` for vertical spacing between major sections
- **Card Content**: `gap-4` for internal spacing
- **List Items**: `gap-3` for item spacing
- **Margins**: `mt-3`, `mb-3` for specific spacing needs

### Layout Patterns
- **Main Dashboard**: `flex flex-col min-h-0` with `overflow-y-auto`
- **Responsive Grid**: `flex-col md:flex-row` for mobile-first design
- **Card Layouts**: `flex flex-col` with appropriate overflow handling

## Component Styling Patterns

### Cards
#### Primary Cards
```tsx
className="rounded-3xl bg-gradient-to-br from-white to-purple-50/50 border-2 border-purple-100/50 shadow-xl"
```

#### Interactive Cards (with hover effects)
```tsx
className="shadow-lg hover:shadow-xl transition-all duration-300 rounded-2xl border-2 border-white/50 backdrop-blur-sm cursor-pointer hover:-translate-y-2 hover:scale-105"
```

#### Card Headers
```tsx
className="relative"
// With decorative elements:
// <div className="absolute top-0 right-0 w-8 h-8 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full opacity-20"></div>
```

### Buttons
#### Primary Buttons
```tsx
className="bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 text-white font-semibold py-2 px-4 rounded-xl transition-all duration-200 hover:scale-105 hover:shadow-lg"
```

#### Icon Buttons
```tsx
className="w-12 h-12 rounded-2xl hover:bg-gray-100/50 hover:shadow-md transition-all duration-200 group"
```

### Backgrounds & Gradients

#### Main Background
```tsx
className="bg-gradient-to-br from-background via-background to-accent/5"
```

#### Decorative Backgrounds
```tsx
// Subtle blur effects
className="absolute inset-0 bg-gradient-to-r from-purple-100/50 to-pink-100/50 rounded-3xl blur-xl"

// Activity section background
className="absolute inset-0 bg-gradient-to-r from-blue-100/30 to-cyan-100/30 rounded-3xl blur-xl"
```

#### Text Gradients
```tsx
className="bg-gradient-to-r from-primary via-purple-600 to-pink-600 bg-clip-text text-transparent"
```

### Hover Effects

#### Scale & Transform Effects
```tsx
className="hover:-translate-y-2 hover:scale-105 transition-all duration-300"
```

#### Shadow Transitions
```tsx
className="shadow-lg hover:shadow-xl transition-all duration-300"
```

#### Opacity Transitions
```tsx
className="opacity-0 group-hover:opacity-100 transition-opacity duration-300"
```

## Icon Usage Guidelines

### Icon Sizing
- **Small Icons**: `w-4 h-4` (16px)
- **Medium Icons**: `w-5 h-5` (20px) or `w-6 h-6` (24px)
- **Large Icons**: `w-8 h-8` (32px)

### Icon Containers
```tsx
// Circular containers
className="p-2 bg-gradient-to-r from-purple-200 to-pink-200 rounded-xl"

// Rounded containers
className="w-12 h-12 bg-gradient-to-br from-purple-400 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg"
```

### Icon Colors
- **Primary Icons**: `text-purple-600`
- **Secondary Icons**: `text-gray-600`
- **Muted Icons**: `text-gray-500`
- **Accent Icons**: `text-orange-600`

## Animation & Transitions

### Duration Classes
- **Fast**: `duration-200` (200ms)
- **Medium**: `duration-300` (300ms)
- **Slow**: `duration-500` (500ms)

### Animation Classes
```tsx
// Subtle floating effect
className="animate-bounce"

// Smooth transitions
className="transition-all duration-300"
```

### Transform Effects
```tsx
// Hover lift effect
className="hover:-translate-y-2 hover:scale-105"

// Group hover effects
className="group-hover:opacity-100 group-hover:translate-x-0"
```

## Responsive Design Patterns

### Breakpoint Strategy
- **Mobile First**: Default styles for mobile
- **Tablet**: `md:` prefix for medium screens and up
- **Desktop**: `lg:` prefix for large screens and up

### Responsive Layout Examples
```tsx
// Flex direction changes
className="flex-col md:flex-row"

// Width adjustments
className="w-full md:w-80"

// Display changes
className="hidden md:block"
```

## Sidebar Styling

### Sidebar Container
```tsx
className="w-20 bg-gradient-to-br from-sidebar to-sidebar-foreground/5 border-r border-border/50"
```

### Navigation Items
```tsx
className="w-12 h-12 rounded-2xl hover:bg-gray-100/50 hover:shadow-md transition-all duration-200 group flex items-center justify-center"
```

### Logo Section
```tsx
className="w-12 h-12 bg-gradient-to-br from-purple-400 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg"
```

## Activity Cards

### Color Assignment
```tsx
const activityColors = [
  "pastel-blue", "pastel-mint", "pastel-peach", "pastel-purple",
  "pastel-pink", "pastel-lavender", "pastel-yellow", "pastel-coral", "pastel-teal"
];

// Dynamic color assignment
const colorIndex = Math.abs(session.activity.id) % activityColors.length;
const cardColor = activityColors[colorIndex];
```

### Card Styling
```tsx
style={{
  backgroundColor: `var(--${cardColor})`,
}}
```

## Form Elements

### Input Fields
```tsx
className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
```

### Labels
```tsx
className="block text-sm font-medium text-foreground mb-2"
```

## Accessibility Considerations

### Focus States
- All interactive elements have visible focus states
- Use `ring-2 ring-ring` for focus indicators

### Color Contrast
- Ensure sufficient contrast between text and background colors
- Use semantic color variables for consistent theming

### Hover States
- All interactive elements have hover states
- Use `cursor-pointer` for clickable elements

## Best Practices

### CSS Organization
1. Use Tailwind utility classes as primary styling method
2. Leverage CSS variables for consistent theming
3. Minimize custom CSS classes
4. Use component variants when possible

### Performance
1. Use `transform` and `opacity` for animations (GPU accelerated)
2. Limit the number of animated elements
3. Use `will-change` sparingly

### Maintainability
1. Keep styling consistent across similar components
2. Use semantic class names and CSS variables
3. Document any deviations from the standard patterns

## Component-Specific Guidelines

### Dashboard
- Use gradient backgrounds for visual interest
- Implement consistent spacing between sections
- Ensure proper scrolling behavior on mobile

### Activity Cards
- Apply consistent hover effects
- Use pastel color palette for variety
- Maintain readable text contrast

### Sidebar
- Keep navigation items consistently sized
- Use subtle hover effects
- Ensure proper icon alignment

### Charts
- Use consistent border radius and shadows
- Apply gradient backgrounds for visual appeal
- Maintain chart readability

## Future Considerations

### Dark Mode Enhancements
- Ensure all gradients work well in both themes
- Test color contrast in both modes
- Consider adding theme-specific decorative elements

### Animation Refinements
- Consider adding entrance animations for new content
- Implement loading states with consistent styling
- Add micro-interactions for better user engagement

### Component Library
- Consider creating custom shadcn/ui variants
- Standardize common patterns into reusable components
- Document component usage examples

---

*This document should be updated whenever new styling patterns are introduced or existing ones are modified.*
