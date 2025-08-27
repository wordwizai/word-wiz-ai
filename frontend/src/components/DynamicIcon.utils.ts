import * as LucideIcons from 'lucide-react';

// Create a lookup object with all lucide icons
const icons = {
  ...LucideIcons
};

// Type for lucide icon components
type LucideIconComponent = React.ComponentType<React.SVGProps<SVGSVGElement>>;

/**
 * Convert kebab-case string to PascalCase to match lucide icon exports
 * e.g., "book-open" -> "BookOpen", "arrow-left" -> "ArrowLeft"
 */
export const kebabToPascalCase = (str: string): string => {
  return str
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join('');
};

/**
 * Special case mappings for icons that don't follow standard kebab-case conversion
 * or have different names in lucide
 */
export const specialCaseMappings: Record<string, string> = {
  'gamepad': 'Gamepad2',
  'volume': 'Volume2',
  'loader': 'Loader2',
  'message': 'MessageCircle',
  'map-pin': 'MapPin',
  'thumbs-up': 'ThumbsUp',
  'thumbs-down': 'ThumbsDown',
  'help-circle': 'HelpCircle',
  'check-circle': 'CheckCircle',
  'x-circle': 'XCircle',
  'alert-circle': 'AlertCircle',
  'alert-triangle': 'AlertTriangle',
  'graduation-cap': 'GraduationCap',
  'trending-up': 'TrendingUp',
  'skip-forward': 'SkipForward',
  'skip-back': 'SkipBack',
  'fast-forward': 'FastForward',
  'chevron-left': 'ChevronLeft',
  'chevron-right': 'ChevronRight',
  'chevron-up': 'ChevronUp',
  'chevron-down': 'ChevronDown',
  'arrow-left': 'ArrowLeft',
  'arrow-right': 'ArrowRight',
  'arrow-up': 'ArrowUp',
  'arrow-down': 'ArrowDown',
  'volume-x': 'VolumeX',
  'book-open': 'BookOpen',
};

/**
 * Get lucide icon component by name
 * Supports both kebab-case and PascalCase naming
 */
export const getIconComponent = (iconName: string): LucideIconComponent | null => {
  // Try direct lookup first (for PascalCase names)
  if (icons[iconName as keyof typeof icons]) {
    return icons[iconName as keyof typeof icons] as LucideIconComponent;
  }
  
  // Check special case mappings
  if (specialCaseMappings[iconName]) {
    const mappedName = specialCaseMappings[iconName];
    if (icons[mappedName as keyof typeof icons]) {
      return icons[mappedName as keyof typeof icons] as LucideIconComponent;
    }
  }
  
  // Convert kebab-case to PascalCase and try lookup
  const pascalCaseName = kebabToPascalCase(iconName);
  if (icons[pascalCaseName as keyof typeof icons]) {
    return icons[pascalCaseName as keyof typeof icons] as LucideIconComponent;
  }
  
  return null;
};

/**
 * Get all available icon names
 */
export const getAvailableIconNames = (): string[] => {
  return Object.keys(icons).filter(key => 
    typeof icons[key as keyof typeof icons] === 'function' || 
    typeof icons[key as keyof typeof icons] === 'object'
  );
};

// Export icons for external usage
export { icons };