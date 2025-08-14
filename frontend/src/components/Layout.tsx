import React, { type ReactNode } from "react";
import Sidebar from "./Sidebar";
import MobileNav from "./MobileNav";

type LayoutProps = {
  children: ReactNode;
};

const Layout = ({ children }: LayoutProps) => {
  return (
    <div className="flex h-screen flex-col md:flex-row relative overflow-hidden">
      <div className="hidden md:flex h-full relative z-10">
        <Sidebar />
      </div>
      <div className="relative z-10 flex-1 w-full h-full overflow-y-auto pb-20 md:pb-0">
        {children}
      </div>
      <MobileNav className="fixed bottom-0 w-full md:hidden z-20 h-16 bg-background/95 backdrop-blur-sm border-t border-border" />
    </div>
  );
};

export default Layout;
