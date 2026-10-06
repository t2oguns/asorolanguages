import type { Metadata } from "next";
import { LoginCard } from "../components/login-card";
 
export const metadata: Metadata = {
  title: "Sign in",
  robots: { index: false, follow: false },
};
 
const errorMessages: Record<string, string> = {
  OAuthAccountNotLinked:
    "This email is already linked to a different sign-in method. Use the account you originally signed up with.",
  AccessDenied: "Access was denied. Try again or use another account.",
  Configuration: "Sign-in is temporarily unavailable. Please try again later.",
};
 
const fallbackError = "We couldn't sign you in. Please try again.";
 
export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  const message = error ? (errorMessages[error] ?? fallbackError) : undefined;
 
  return (
    <main className="grid min-h-dvh place-items-center bg-slate-100 px-6 py-12 dark:bg-slate-950">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm sm:p-10 dark:border-slate-800 dark:bg-slate-900">
        <LoginCard error={message} />
      </div>
    </main>
  );
}