import {
  Bean,
  BedDouble,
  Bird,
  Blocks,
  BookOpen,
  Bot,
  BrickWall,
  CakeSlice,
  Circle,
  Citrus,
  Cloud,
  Coins,
  Cookie,
  CookingPot,
  Crown,
  Dog,
  Drama,
  Flame,
  Footprints,
  Ghost,
  Hammer,
  Infinity as InfinityIcon,
  Map as MapIcon,
  Megaphone,
  MountainSnow,
  Music,
  PawPrint,
  Rabbit,
  Rat,
  Rocket,
  Shell,
  Ship,
  ShoppingBasket,
  Snowflake,
  Soup,
  Sprout,
  Tent,
  TreePalm,
  Turtle,
  Wand,
  WandSparkles,
  Wheat,
  type LucideIcon,
} from 'lucide-react';

// Only the icons activities actually use (emoji_icon in
// backend/dev/seed_activities.json and backend/scripts/new_activities.json).
// `import * as` pulled in all ~1,500 lucide icons, about 700 KB of
// JavaScript on the dashboard and practice pages. A new activity with an
// icon that isn't listed here shows the fallback until it's added.
const icons: Record<string, LucideIcon> = {
  Bean,
  BedDouble,
  Bird,
  Blocks,
  BookOpen,
  Bot,
  BrickWall,
  CakeSlice,
  Circle,
  Citrus,
  Cloud,
  Coins,
  Cookie,
  CookingPot,
  Crown,
  Dog,
  Drama,
  Flame,
  Footprints,
  Ghost,
  Hammer,
  Infinity:InfinityIcon,
  Map: MapIcon,
  Megaphone,
  MountainSnow,
  Music,
  PawPrint,
  Rabbit,
  Rat,
  Rocket,
  Shell,
  Ship,
  ShoppingBasket,
  Snowflake,
  Soup,
  Sprout,
  Tent,
  TreePalm,
  Turtle,
  Wand,
  WandSparkles,
  Wheat,
};

// Type for lucide icon components
type LucideIconComponent = React.ComponentType<React.SVGProps<SVGSVGElement>>;

/**
 * Get lucide icon component by name
 * Uses the exact case that lucide exports (PascalCase)
 */
export const getIconComponent = (iconName: string): LucideIconComponent | null => {
  return (icons[iconName] as LucideIconComponent | undefined) ?? null;
};

/**
 * Get all available icon names
 */
export const getAvailableIconNames = (): string[] => Object.keys(icons);

// Export icons for external usage
export { icons };
