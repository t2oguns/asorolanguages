import type { ButtonHTMLAttributes } from 'react';
import { focusRing } from './ui';

export type OptionState = 'idle' | 'selected' | 'correct' | 'wrong';

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { state?: OptionState };

/** Full-width answer card used by choice, fill, and match exercises. */
export default function OptionButton({ state = 'idle', className = '', ...props }: Props) {
  return (
    <button
      type="button"
      data-state={state}
      className={[
        'w-full rounded-2xl border-2 border-slate-200 bg-white px-4 py-4 text-left text-lg text-slate-900',
        'transition-colors motion-reduce:transition-none',
        'enabled:hover:border-blue-600 disabled:cursor-default',
        'data-[state=selected]:border-blue-600 data-[state=selected]:bg-blue-50',
        'data-[state=correct]:border-emerald-600 data-[state=correct]:bg-emerald-50',
        'data-[state=wrong]:border-red-500 data-[state=wrong]:bg-red-50',
        focusRing,
        className,
      ].join(' ')}
      {...props}
    />
  );
}