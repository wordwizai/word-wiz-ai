import { Link } from "react-router-dom";

const LandingPageFooter = () => {
  return (
    <footer className="bg-primary text-primary-foreground py-12 px-6 mt-12">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="text-center md:text-left">
            <h3 className="text-xl font-bold mb-2">Word Wiz AI</h3>
            <p className="text-sm">Read smarter. Grow faster.</p>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="font-semibold mb-3 text-sm uppercase">Product</h4>
            <div className="flex flex-col gap-2 text-sm">
              <Link to="/about" className="hover:underline">
                About
              </Link>
              <Link to="/signup" className="hover:underline">
                Sign Up
              </Link>
              <Link to="/login" className="hover:underline">
                Login
              </Link>
              <Link to="/contact" className="hover:underline">
                Contact
              </Link>
            </div>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold mb-3 text-sm uppercase">Resources</h4>
            <div className="flex flex-col gap-2 text-sm">
              <Link
                to="#"
                onClick={(e) => {
                  e.preventDefault();
                  alert("Coming soon");
                }}
                className="hover:underline"
              >
                For Educators
              </Link>
              <Link
                to="#"
                onClick={(e) => {
                  e.preventDefault();
                  alert("Coming soon");
                }}
                className="hover:underline"
              >
                Privacy Policy
              </Link>
              <Link
                to="#"
                onClick={(e) => {
                  e.preventDefault();
                  alert("Coming soon");
                }}
                className="hover:underline"
              >
                Terms of Service
              </Link>
            </div>
          </div>

          {/* Comparisons */}
          <div>
            <h4 className="font-semibold mb-3 text-sm uppercase">
              Comparisons
            </h4>
            <div className="flex flex-col gap-2 text-sm">
              <Link
                to="/comparisons/abcmouse-vs-hooked-on-phonics-vs-word-wiz-ai"
                className="hover:underline"
              >
                ABCmouse vs HOP
              </Link>
              <Link
                to="/comparisons/reading-eggs-vs-starfall-vs-word-wiz-ai"
                className="hover:underline"
              >
                Reading Eggs vs Starfall
              </Link>
              <Link
                to="/comparisons/homer-vs-khan-academy-kids-vs-word-wiz-ai"
                className="hover:underline"
              >
                HOMER vs Khan Kids
              </Link>
              <Link
                to="/comparisons/best-free-reading-apps"
                className="hover:underline"
              >
                Best Free Apps
              </Link>
            </div>
          </div>
        </div>

        {/* Copyright */}
        <div className="border-t border-primary-foreground/20 pt-6 text-center text-sm">
          <p>
            &copy; {new Date().getFullYear()} Word Wiz AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default LandingPageFooter;
