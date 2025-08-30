import * as LucideIcons from 'lucide-react';

// Create a lookup object with all lucide icons
const icons = {
  ...LucideIcons
};

// Type for lucide icon components
type LucideIconComponent = React.ComponentType<React.SVGProps<SVGSVGElement>>;

/**
 * Get lucide icon component by name
 * Uses the exact case that lucide exports (PascalCase)
 */
export const getIconComponent = (iconName: string): LucideIconComponent | null => {
  if (icons[iconName as keyof typeof icons]) {
    return icons[iconName as keyof typeof icons] as LucideIconComponent;
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