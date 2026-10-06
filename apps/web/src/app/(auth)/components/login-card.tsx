"use client";

import { useState } from "react";
import { GitHubIcon, GoogleIcon } from "./provider-icons";
import { login } from "../lib/login";

type ProviderId = "google" | "github";

const providers: {
  id: ProviderId;
  name: string;
  Icon: (props: { className?: string }) => React.JSX.Element;
}[] = [
  { id: "google", name: "Google", Icon: GoogleIcon },
  { id: "github", name: "GitHub", Icon: GitHubIcon },
];

function Spinner({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      focusable="false"
      className={`animate-spin motion-reduce:animate-none ${className ?? ""}`}
    >
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" className="opacity-25" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function LoginCard({ error }: { error?: string }) {
  const [pending, setPending] = useState<ProviderId | null>(null);


  return (
    <div className="w-full max-w-sm">
      <div className="mb-8 flex items-center gap-3">
        <span
          aria-hidden="true"
          className="grid size-9 place-items-center rounded-lg bg-slate-900 text-sm font-semibold text-white dark:bg-slate-100 dark:text-slate-900"
        >
          A
        </span>
        <span className="text-base font-semibold tracking-tight text-slate-900 dark:text-slate-100">
          Asoro
        </span>
      </div>

      <h1 className="text-balance text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
        Sign in to your account
      </h1>
      <p className="mt-2 text-pretty text-sm leading-6 text-slate-600 dark:text-slate-400">
        Use one of your existing accounts. We don&apos;t use or store passwords.
      </p>

      {error ? (
        <div
          role="alert"
          className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm leading-5 text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200"
        >
          {error}
        </div>
      ) : null}

      <div className="mt-8 flex flex-col gap-3">
        {providers.map(({ id, name, Icon }) => {
          const isPending = pending === id;
          return (
            <button
              key={id}
              type="button"
              onClick={()=>login(id)}
              disabled={pending !== null}
              aria-busy={isPending}
              className="flex w-full items-center justify-center gap-3 rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm font-medium text-slate-900 shadow-sm transition-colors hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-700 disabled:cursor-not-allowed disabled:opacity-60 motion-reduce:transition-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800 dark:focus-visible:outline-sky-400"
            >
              {isPending ? <Spinner className="size-5" /> : <Icon className="size-5" />}
              <span>{isPending ? `Opening ${name}…` : `Continue with ${name}`}</span>
            </button>
          );
        })}
      </div>

      <p className="mt-8 text-xs leading-5 text-slate-500 dark:text-slate-400">
        By continuing, you agree to our{" "}
        <a
          href="/terms"
          className="underline underline-offset-2 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-700 dark:hover:text-slate-100 dark:focus-visible:outline-sky-400"
        >
          Terms of Service
        </a>{" "}
        and{" "}
        <a
          href="/privacy"
          className="underline underline-offset-2 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-700 dark:hover:text-slate-100 dark:focus-visible:outline-sky-400"
        >
          Privacy Policy
        </a>
        .
      </p>
    </div>
  );
}