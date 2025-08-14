import { type Variant } from "framer-motion";

// Define a custom type for variants since Variants might not be exported in this version
type CustomVariants = {
  [key: string]: Variant;
};

// Page transition animations
export const pageVariants: CustomVariants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  in: {
    opacity: 1,
    y: 0,
  },
  out: {
    opacity: 0,
    y: -20,
  },
};

export const pageTransition = {
  type: "tween",
  ease: "anticipate",
  duration: 0.4,
};

// Fade animations
export const fadeInUp: CustomVariants = {
  hidden: {
    opacity: 0,
    y: 30,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: "easeOut",
    },
  },
};

export const fadeInLeft: CustomVariants = {
  hidden: {
    opacity: 0,
    x: -30,
  },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.5,
      ease: "easeOut",
    },
  },
};

export const fadeInRight: CustomVariants = {
  hidden: {
    opacity: 0,
    x: 30,
  },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.5,
      ease: "easeOut",
    },
  },
};

// Stagger container animation
export const staggerContainer: CustomVariants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

export const staggerChild: CustomVariants = {
  hidden: {
    opacity: 0,
    y: 20,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: "easeOut",
    },
  },
};

// Scale animations
export const scaleIn: CustomVariants = {
  hidden: {
    opacity: 0,
    scale: 0.8,
  },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.4,
      ease: "easeOut",
    },
  },
};

export const scaleOnHover = {
  scale: 1.05,
  transition: {
    type: "spring",
    stiffness: 300,
    damping: 20,
  },
};

export const scaleOnTap = {
  scale: 0.95,
  transition: {
    type: "spring",
    stiffness: 400,
    damping: 17,
  },
};

// Button animations
export const buttonHover = {
  scale: 1.05,
  y: -2,
  boxShadow: "0 10px 25px rgba(0,0,0,0.1)",
  transition: {
    type: "spring",
    stiffness: 300,
    damping: 20,
  },
};

export const buttonTap = {
  scale: 0.98,
  y: 0,
  transition: {
    type: "spring",
    stiffness: 400,
    damping: 17,
  },
};

// Card animations
export const cardHover = {
  y: -8,
  scale: 1.02,
  boxShadow: "0 20px 25px rgba(0,0,0,0.1)",
  transition: {
    type: "spring",
    stiffness: 300,
    damping: 20,
  },
};

// Form animations
export const formFieldVariants: CustomVariants = {
  hidden: {
    opacity: 0,
    y: 20,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: "easeOut",
    },
  },
};

export const formContainerVariants: CustomVariants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

// Loading animations
export const spinVariants: CustomVariants = {
  animate: {
    rotate: 360,
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: "linear",
    },
  },
};

export const pulseVariants: CustomVariants = {
  animate: {
    scale: [1, 1.05, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
};

// Navigation animations
export const slideInLeft: CustomVariants = {
  hidden: {
    x: "-100%",
    opacity: 0,
  },
  visible: {
    x: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30,
    },
  },
  exit: {
    x: "-100%",
    opacity: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30,
    },
  },
};

export const slideInRight: CustomVariants = {
  hidden: {
    x: "100%",
    opacity: 0,
  },
  visible: {
    x: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30,
    },
  },
  exit: {
    x: "100%",
    opacity: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30,
    },
  },
};

export const slideUp: CustomVariants = {
  hidden: {
    y: "100%",
    opacity: 0,
  },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30,
    },
  },
  exit: {
    y: "100%",
    opacity: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30,
    },
  },
};

// Icon animations
export const iconHover = {
  scale: 1.1,
  rotate: 5,
  transition: {
    type: "spring",
    stiffness: 300,
    damping: 20,
  },
};

export const iconTap = {
  scale: 0.9,
  rotate: -5,
  transition: {
    type: "spring",
    stiffness: 400,
    damping: 17,
  },
};

// Bounce animation
export const bounceIn: CustomVariants = {
  hidden: {
    opacity: 0,
    scale: 0.3,
  },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 260,
      damping: 20,
    },
  },
};