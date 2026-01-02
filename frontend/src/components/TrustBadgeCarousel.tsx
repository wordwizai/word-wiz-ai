import { useEffect, useRef, useState } from "react";
import { CircleDollarSign, Sparkles, Award, Shield, Clock, Zap } from "lucide-react";

const TRUST_BADGES = [
  {
    icon: Award,
    text: "2nd Place Congressional App Challenge Winner",
    color: "text-yellow-600",
  },
  {
    icon: Sparkles,
    text: "Ed Tech Indexed (Official App)",
    color: "text-blue-600",
  },
  {
    icon: Shield,
    text: "Backed with Real AI Research",
    color: "text-purple-600",
  },
  {
    icon: CircleDollarSign,
    text: "100% Free",
    color: "text-green-600",
  },
  {
    icon: Shield,
    text: "100% Data Safety",
    color: "text-red-600",
  },
  {
    icon: Clock,
    text: "2 Clicks to Set Up",
    color: "text-orange-600",
  },
];

const TrustBadgeCarousel = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % TRUST_BADGES.length);
    }, 3000); // 3 second latency as requested

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      const badgeWidth = scrollRef.current.scrollWidth / (TRUST_BADGES.length * 2);
      scrollRef.current.scrollTo({
        left: badgeWidth * currentIndex,
        behavior: "smooth",
      });
    }
  }, [currentIndex]);

  return (
    <div className="relative w-full overflow-hidden">
      {/* Fade gradients on edges */}
      <div className="absolute left-0 top-0 bottom-0 w-12 bg-gradient-to-r from-background to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-background to-transparent z-10 pointer-events-none" />
      
      <div
        ref={scrollRef}
        className="flex gap-3 overflow-x-hidden py-2 px-4"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {/* Duplicate badges for seamless loop */}
        {[...TRUST_BADGES, ...TRUST_BADGES].map((badge, idx) => {
          const Icon = badge.icon;
          return (
            <div
              key={idx}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-muted/50 rounded-md border whitespace-nowrap flex-shrink-0"
            >
              <Icon className={`w-4 h-4 ${badge.color}`} />
              <span className="font-medium text-sm text-muted-foreground">
                {badge.text}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TrustBadgeCarousel;
