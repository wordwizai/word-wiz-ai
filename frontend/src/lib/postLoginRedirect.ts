// Where to send someone after they sign in, set when a protected page bounces
// them to /login. sessionStorage (not router state) so it survives the
// Google OAuth round trip through the backend.
const POST_LOGIN_REDIRECT_KEY = "wordwiz.postLoginRedirect";

export function rememberPostLoginRedirect(path: string) {
  try {
    sessionStorage.setItem(POST_LOGIN_REDIRECT_KEY, path);
  } catch {
    // Storage blocked (private mode); they'll land on the dashboard instead.
  }
}

export function consumePostLoginRedirect(): string {
  try {
    const path = sessionStorage.getItem(POST_LOGIN_REDIRECT_KEY);
    sessionStorage.removeItem(POST_LOGIN_REDIRECT_KEY);
    // Only same-site paths; "//evil.com" would be protocol-relative.
    if (path && path.startsWith("/") && !path.startsWith("//")) return path;
  } catch {
    // fall through
  }
  return "/dashboard";
}
