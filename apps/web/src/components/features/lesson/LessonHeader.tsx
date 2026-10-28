import { focusRing } from './ui/ui';

type Props = { progress: number; title?: string; onExit: () => void };

export default function LessonHeader({ progress, title, onExit }: Props) {
  return (
    <header className="mx-auto flex w-full max-w-[720px] items-center gap-4 px-5 py-4">
      <button
        type="button"
        onClick={onExit}
        aria-label="Exit lesson"
        className={`size-10 flex-none rounded-full text-lg text-slate-500 hover:bg-slate-200 ${focusRing}`}
      >
        ✕
      </button>
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progress)}
        aria-label={title ?? 'Lesson progress'}
        className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-200"
      >
        <div
          className="h-full rounded-full bg-blue-600 transition-[width] duration-300 motion-reduce:transition-none"
          style={{ width: `${progress}%` }}
        />
      </div>
    </header>
  );
}