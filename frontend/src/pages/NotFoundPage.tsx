import { useContext } from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Button } from "@/components/ui/button";
import { AuthContext } from "@/contexts/AuthContext";
import Mascot from "@/components/mascot/Mascot";

// Every unknown URL lands here: typos, old bookmarks, renamed pages. It used
// to say the site was "under construction", which read as if the whole app
// were broken.
const NotFoundPage = () => {
  const { token } = useContext(AuthContext);

  return (
    <main className="flex min-h-screen w-full items-center justify-center bg-background p-6">
      <Helmet>
        <title>Page not found | Word Wiz AI</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <div className="max-w-md space-y-5 text-center">
        <Mascot mood="idle" className="mx-auto size-16" />
        <h1 className="text-3xl font-bold text-foreground">
          We can't find that page
        </h1>
        <p className="text-muted-foreground">
          The link may be old or have a typo in it. Everything else is working
          fine.
        </p>
        <div className="flex flex-col justify-center gap-3 sm:flex-row">
          {token && (
            <Button asChild className="rounded-xl">
              <Link to="/dashboard">Go to your dashboard</Link>
            </Button>
          )}
          <Button
            asChild
            variant={token ? "outline" : "default"}
            className="rounded-xl"
          >
            <Link to="/">Back to home</Link>
          </Button>
        </div>
      </div>
    </main>
  );
};

export default NotFoundPage;
