import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { spinVariants } from "@/lib/animations";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
  text?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = "md", 
  className = "",
  text = "Loading..."
}) => {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-8 h-8", 
    lg: "w-12 h-12"
  };

  return (
    <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
      <motion.div
        variants={spinVariants}
        animate="animate"
        className={`${sizeClasses[size]} text-primary`}
      >
        <Loader2 className="w-full h-full" />
      </motion.div>
      {text && (
        <motion.p 
          className="text-sm text-muted-foreground"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          {text}
        </motion.p>
      )}
    </div>
  );
};

export default LoadingSpinner;