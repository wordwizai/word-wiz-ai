import { CircleDollarSign, Sparkles, Award, Shield, Clock } from "lucide-react";

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
  return (
    <div className="relative w-full overflow-hidden">
      {/* Fade gradients on edges */}
      <div className="absolute left-0 top-0 bottom-0 w-12 bg-gradient-to-r from-background to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-background to-transparent z-10 pointer-events-none" />
      
      <div className="flex gap-3 py-2 px-4 overflow-hidden">
        {/* Animate continuously with CSS */}
        <div className="flex gap-3 animate-scroll-left">
          {/* Triple the badges for seamless infinite scroll */}
          {[...TRUST_BADGES, ...TRUST_BADGES, ...TRUST_BADGES].map((badge, idx) => {
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
      
      {/* CSS animation styles */}
      <style>{`
        @keyframes scroll-left {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-33.333%);
          }
        }
        
        .animate-scroll-left {
          animation: scroll-left 20s linear infinite;
        }
        
        .animate-scroll-left:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
};

export default TrustBadgeCarousel;
