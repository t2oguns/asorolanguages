import AudioButton from '../ui/AudioButton';
import type { ExerciseProps } from '../types';

export default function Intro({ ex, locale }: ExerciseProps<'intro'>) {
  return (
    <div className="mt-[8vh] flex flex-col items-center gap-3 rounded-3xl border-2 border-slate-200 bg-white px-6 py-9 text-center">
      <p className="text-[0.95rem] font-semibold text-slate-500">New word</p>
      <p className="flex items-center gap-3 text-[clamp(2rem,6vw,2.8rem)] font-bold">
        <AudioButton text={ex.speak ?? ex.term} locale={locale} />
        <span>{ex.term}</span>
      </p>
      <p className="text-xl text-slate-500">{ex.translation}</p>
      {ex.note && <p className="text-slate-500">{ex.note}</p>}
    </div>
  );
}