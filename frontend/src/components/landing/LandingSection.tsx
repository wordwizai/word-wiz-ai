import type { ReactNode } from "react";
import { motion } from "framer-motion";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 },
};

/** A home page section that fades up as it scrolls into view. */
const LandingSection = ({
  id,
  className,
  children,
}: {
  id?: string;
  className?: string;
  children: ReactNode;
}) => (
  <motion.section
    id={id}
    className={className}
    variants={fadeUp}
    initial="hidden"
    whileInView="visible"
    // Low, so a tall section on a phone shows up as soon as it starts
    viewport={{ once: true, amount: 0.15 }}
    transition={{ duration: 0.6 }}
  >
    {children}
  </motion.section>
);

export default LandingSection;
