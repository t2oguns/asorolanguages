import type { ButtonHTMLAttributes } from 'react';
import { focusRing } from './ui';
 
type Props = ButtonHTMLAttributes<HTMLButtonElement> & { used?: boolean };
 
/** Tappable word used by the word bank exercise. */
export default function WordTile({ used = false, className = '', ...props }: Props) {
  return (
    <button
      type="button"
      data-used={used}
      className={[
        'rounded-xl border-2 border-slate-200 bg-white px-4 py-2.5 text-lg',
        'enabled:hover:border-blue-600 disabled:cursor-default data-[used=true]:opacity-30',
        focusRing,
        className,
      ].join(' ')}
      {...props}
    />
  );
}
 