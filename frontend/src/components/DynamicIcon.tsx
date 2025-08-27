import React from 'react';
import { getIconComponent, icons } from './DynamicIcon.utils';

// Type for lucide icon components
type LucideIconComponent = React.ComponentType<React.SVGProps<SVGSVGElement>>;

export interface DynamicIconProps {
  /**
   * The name of the lucide icon to display
   * Can be kebab-case (e.g., "book-open") or PascalCase (e.g., "BookOpen")
   */
  name: string;
  /**
   * Size of the icon (CSS class or pixel value)
   */
  size?: string | number;
  /**
   * Additional CSS classes
   */
  className?: string;
  /**
   * Color of the icon
   */
  color?: string;
  /**
   * Fallback icon name if the requested icon is not found
   */
  fallback?: string;
}

/**
 * DynamicIcon component that renders lucide icons based on string names
 * Supports all lucide icons with automatic name conversion from kebab-case to PascalCase
 * 
 * @example
 * <DynamicIcon name="play" size="24" className="text-blue-500" />
 * <DynamicIcon name="BookOpen" size="6xl" />
 * <DynamicIcon name="book-open" size="6xl" />
 * <DynamicIcon name="invalid-icon" fallback="circle" />
 */
export const DynamicIcon: React.FC<DynamicIconProps> = ({
  name,
  size = 24,
  className = '',
  color,
  fallback = 'circle'
}) => {
  // Get the icon component
  let IconComponent = getIconComponent(name);
  
  // If not found, try fallback
  if (!IconComponent && fallback) {
    IconComponent = getIconComponent(fallback);
  }
  
  // Final fallback to Circle icon
  if (!IconComponent) {
    IconComponent = icons.Circle as LucideIconComponent;
  }
  
  // Handle size prop - if it's a number, convert to pixel string
  // If it's a Tailwind class like "6xl", use it as className
  const sizeProps = typeof size === 'number' ? { size } : {};
  const sizeClass = typeof size === 'string' && isNaN(Number(size)) ? size : '';
  
  // Build final className
  const finalClassName = [
    sizeClass,
    className
  ].filter(Boolean).join(' ');
  
  return (
    <IconComponent 
      {...sizeProps}
      className={finalClassName}
      color={color}
    />
  );
};

export default DynamicIcon;