import { focusRing } from '../ui/ui';

type Props = { title?: string; firstTry: number; total: number; onFinish: () => void };

export default function LessonComplete({ title, firstTry, total, onFinish }: Props) {
  const pct = Math.round((total ? firstTry / total : 1) * 100);
  return (
    <main className="mx-auto flex w-full max-w-[480px] flex-1 flex-col items-center justify-center gap-5 px-5 py-12 text-center">
      <h1 className="text-3xl font-bold">Lesson complete</h1>
      {title && <p className="text-slate-500">{title}</p>}
      <dl className="grid w-full grid-cols-2 gap-3">
        <div className="rounded-2xl border-2 border-slate-200 bg-white p-4">
          <dt className="text-sm text-slate-500">Correct first try</dt>
          <dd className="mt-1 text-2xl font-bold">
            {firstTry} of {total}
          </dd>
        </div>
        <div className="rounded-2xl border-2 border-slate-200 bg-white p-4">
          <dt className="text-sm text-slate-500">Accuracy</dt>
          <dd className="mt-1 text-2xl font-bold">{pct}%</dd>
        </div>
      </dl>
      <button
        type="button"
        onClick={onFinish}
        className={`min-w-36 rounded-2xl bg-blue-600 px-7 py-3.5 font-bold text-white ${focusRing}`}
      >
        Finish
      </button>
    </main>
  );
}