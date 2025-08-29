import { Link } from "react-router-dom";

const LandingPageFooter = () => {
  return (
    <footer className="bg-primary text-primary-foreground py-8 px-6 mt-12">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 md:gap-0">
        <div className="mb-4 md:mb-0 text-center md:text-left">
          <h3 className="text-xl font-bold">Word Wiz AI</h3>
          <p className="text-sm">Read smarter. Grow faster.</p>
        </div>
        <div className="flex flex-wrap justify-center md:justify-start gap-4 text-sm">
          {[
            { name: "About", path: "/about" },
            { name: "Contact", path: "/contact" },
            { name: "Privacy", path: "#" },
            { name: "Terms", path: "#" },
            { name: "For Educators", path: "#" },
          ].map((link, index) => (
            <Link
              key={index}
              to={link.path}
              className="hover:underline text-primary-foreground"
              onClick={(e) => {
                if (link.path === "#") {
                  e.preventDefault();
                  alert("This page is not available yet.");
                }
              }}
            >
              {link.name}
            </Link>
          ))}
        </div>
      </div>
    </footer>
  );
};

export default LandingPageFooter;
