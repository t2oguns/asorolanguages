import Prompt from '../ui/Prompt';
import type { ExerciseProps } from '../types';

export default function TypeIn({ ex, value, onChange, locked, locale, status }: ExerciseProps) {
  return <>
    <Prompt ex={ex} locale={locale} />
    <input data-status={status} value={typeof value === 'string' ? value : ''} onChange={(event) => onChange(event.target.value)}
      disabled={locked} autoFocus autoCapitalize="off" autoCorrect="off" spellCheck={false} aria-label="Your answer"
      className="w-full rounded-2xl border-2 border-slate-200 bg-white px-4 py-4 text-xl focus:border-blue-600 focus:outline-none data-[status=correct]:border-emerald-600 data-[status=correct]:bg-emerald-50 data-[status=wrong]:border-red-500 data-[status=wrong]:bg-red-50" />
  </>;
}
