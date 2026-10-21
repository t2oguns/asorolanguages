import React from 'react'
import { login } from "../../../app/(auth)/lib/login";

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

const SocialLoginButton = ({id, name, pending, Icon}: {id: string,name: string, pending: string | null, Icon: (props: { className?: string }) => React.JSX.Element}) => {
    const isPending = pending === id;
  return (
    <button
        type="button"
        onClick={()=>login(id)}
        disabled={pending !== null}
        name={`Continue with ${name}`}
        aria-busy={isPending}
        className="flex w-full items-center justify-center gap-3 rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm font-medium text-slate-900 shadow-sm transition-colors hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-700 disabled:cursor-not-allowed disabled:opacity-60 motion-reduce:transition-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800 dark:focus-visible:outline-sky-400"
    >
        {isPending ? <Spinner className="size-5" /> : <Icon className="size-5" />}
        <span>{isPending ? `Opening ${name}…` : `Continue with ${name}`}</span>
    </button>
  )
}

export default SocialLoginButton