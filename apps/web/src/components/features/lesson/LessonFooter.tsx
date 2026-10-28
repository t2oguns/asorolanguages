import type { Status } from './types';
import { column, focusRing } from './ui/ui';

type Props = {
  status: Status;
  ready: boolean;
  label: string;
  wrongTitle: string;
  detail: string;
  onPrimary: () => void;
};

/** Bottom bar: Check / Continue button plus correct / wrong feedback. */
export default function LessonFooter({ status, ready, label, wrongTitle, detail, onPrimary }: Props) {
  return (
    <footer
      data-status={status}
      className={[
        'group fixed inset-x-0 bottom-0 border-t-2 border-slate-200 bg-white px-5 pt-4',
        'pb-[calc(1rem+env(safe-area-inset-bottom,0px))]',
        'data-[status=correct]:border-emerald-600 data-[status=correct]:bg-emerald-50',
        'data-[status=wrong]:border-red-500 data-[status=wrong]:bg-red-50',
      ].join(' ')}
    >
      <div className={`${column} flex min-h-[52px] items-center justify-between gap-4`}>
        <div className="min-w-0" aria-live="polite">
          {status === 'correct' && (
            <p className="text-lg font-bold text-emerald-700">Correct</p>
          )}
          {status === 'wrong' && (
            <>
              <p className="text-lg font-bold text-red-600">{wrongTitle}</p>
              <p className="mt-0.5 [overflow-wrap:anywhere]">{detail}</p>
            </>
          )}
        </div>
        <button
          type="button"
          onClick={onPrimary}
          disabled={!ready}
          className={[
            'min-w-36 flex-none rounded-2xl bg-blue-600 px-7 py-3.5 font-bold text-white',
            'disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-500',
            'group-data-[status=correct]:bg-emerald-600 group-data-[status=wrong]:bg-red-500',
            focusRing,
          ].join(' ')}
        >
          {label}
        </button>
      </div>
    </footer>
  );
}