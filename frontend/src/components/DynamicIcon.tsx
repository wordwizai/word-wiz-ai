import React from 'react';
import {
  // Activity & Play icons
  Play,
  Pause,
  SkipForward,
  SkipBack,
  FastForward,
  Rewind,
  
  // Media & Content icons
  BookOpen,
  Book,
  Mic,
  Volume2,
  VolumeX,
  Music,
  Headphones,
  
  // Learning & Education icons
  Target,
  TrendingUp,
  Award,
  Star,
  Trophy,
  GraduationCap,
  Brain,
  
  // Interface icons
  Home,
  Settings,
  User,
  Users,
  Bell,
  Search,
  Menu,
  X,
  Check,
  AlertCircle,
  Info,
  
  // Arrows & Navigation
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  
  // Common UI icons
  Heart,
  ThumbsUp,
  ThumbsDown,
  Clock,
  Calendar,
  Mail,
  Phone,
  MapPin,
  
  // Activity types
  Gamepad2,
  Zap,
  Lightbulb,
  Palette,
  Camera,
  Video,
  
  // Social & Communication
  MessageCircle,
  Share,
  Github,
  Twitter,
  Instagram,
  Linkedin,
  
  // Utility & Status
  Loader2,
  CheckCircle,
  XCircle,
  AlertTriangle,
  HelpCircle,
  Plus,
  Minus,
  
  // Default fallback
  Circle,
  
  // Special UI effects
  Sparkles,
} from 'lucide-react';

// Icon mapping object
const iconMap = {
  // Activity & Play icons
  'play': Play,
  'pause': Pause,
  'skip-forward': SkipForward,
  'skip-back': SkipBack,
  'fast-forward': FastForward,
  'rewind': Rewind,
  
  // Media & Content icons
  'book-open': BookOpen,
  'book': Book,
  'mic': Mic,
  'volume': Volume2,
  'volume-x': VolumeX,
  'music': Music,
  'headphones': Headphones,
  
  // Learning & Education icons
  'target': Target,
  'trending-up': TrendingUp,
  'award': Award,
  'star': Star,
  'trophy': Trophy,
  'graduation-cap': GraduationCap,
  'brain': Brain,
  
  // Interface icons
  'home': Home,
  'settings': Settings,
  'user': User,
  'users': Users,
  'bell': Bell,
  'search': Search,
  'menu': Menu,
  'x': X,
  'check': Check,
  'alert-circle': AlertCircle,
  'info': Info,
  
  // Arrows & Navigation
  'arrow-left': ArrowLeft,
  'arrow-right': ArrowRight,
  'arrow-up': ArrowUp,
  'arrow-down': ArrowDown,
  'chevron-left': ChevronLeft,
  'chevron-right': ChevronRight,
  'chevron-up': ChevronUp,
  'chevron-down': ChevronDown,
  
  // Common UI icons
  'heart': Heart,
  'thumbs-up': ThumbsUp,
  'thumbs-down': ThumbsDown,
  'clock': Clock,
  'calendar': Calendar,
  'mail': Mail,
  'phone': Phone,
  'map-pin': MapPin,
  
  // Activity types
  'gamepad': Gamepad2,
  'zap': Zap,
  'lightbulb': Lightbulb,
  'palette': Palette,
  'camera': Camera,
  'video': Video,
  
  // Social & Communication
  'message': MessageCircle,
  'share': Share,
  'github': Github,
  'twitter': Twitter,
  'instagram': Instagram,
  'linkedin': Linkedin,
  
  // Utility & Status
  'loader': Loader2,
  'check-circle': CheckCircle,
  'x-circle': XCircle,
  'alert-triangle': AlertTriangle,
  'help-circle': HelpCircle,
  'plus': Plus,
  'minus': Minus,
} as const;

export interface DynamicIconProps {
  /**
   * The name of the lucide icon to display
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
 * 
 * @example
 * <DynamicIcon name="play" size="24" className="text-blue-500" />
 * <DynamicIcon name="star" size="6xl" />
 * <DynamicIcon name="invalid-icon" fallback="circle" />
 */
export const DynamicIcon: React.FC<DynamicIconProps> = ({
  name,
  size = 24,
  className = '',
  color,
  fallback = 'circle'
}) => {
  // Get the icon component from the map
  const IconComponent = iconMap[name as keyof typeof iconMap] || iconMap[fallback as keyof typeof iconMap] || Circle;
  
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

// Export the icon map for external usage if needed
export { iconMap };

// Export a helper function to get available icon names
export const getAvailableIconNames = (): string[] => {
  return Object.keys(iconMap);
};

export default DynamicIcon;