import React, { type ReactNode } from "react";
import Sidebar from "./Sidebar";
import MobileNav from "./MobileNav";

type LayoutProps = {
  children: ReactNode;
};

const Layout = ({ children }: LayoutProps) => {
  return (
    <div className="flex h-screen flex-col md:flex-row">
      <div className="hidden md:flex h-full">
        <Sidebar />
      </div>
      {children}
      <MobileNav className="fixed bottom-0 w-full md:hidden" />
    </div>
  );
};

export default Layout;
