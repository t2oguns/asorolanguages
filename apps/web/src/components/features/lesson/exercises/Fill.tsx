import ExerciseHeading from '../ui/ExerciseHeading';
import OptionButton, { type OptionState } from '../ui/OptionButton';
import type { ExerciseProps } from '../types';

export default function Fill({ ex, value, onChange, locked }: ExerciseProps<'fill'>) {
  const chosen = typeof value === 'number' ? ex.options[value] : '';

  const stateOf = (i: number): OptionState => {
    if (!locked) return value === i ? 'selected' : 'idle';
    if (i === ex.answer) return 'correct';
    if (i === value) return 'wrong';
    return 'idle';
  };

  return (
    <>
      <ExerciseHeading instruction={ex.instruction ?? 'Fill in the missing word'} />

      <p className="text-[clamp(1.4rem,3.6vw,1.8rem)] font-semibold leading-relaxed">
        {ex.before}{' '}
        <span
          data-filled={chosen !== ''}
          className="inline-block min-w-24 border-b-[3px] border-slate-200 px-2 text-center text-blue-600 data-[filled=true]:border-blue-600"
        >
          {chosen || '\u00A0'}
        </span>{' '}
        {ex.after}
      </p>
      {ex.translation && <p className="text-slate-500">{ex.translation}</p>}

      <div className="grid content-start gap-2.5">
        {ex.options.map((option, i) => (
          <OptionButton
            key={i}
            state={stateOf(i)}
            disabled={locked}
            onClick={() => onChange(i)}
          >
            {option}
          </OptionButton>
        ))}
      </div>
    </>
  );
}