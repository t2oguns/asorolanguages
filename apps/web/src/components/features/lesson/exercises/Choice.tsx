import ExerciseHeading from '../ui/ExerciseHeading';
import OptionButton, { type OptionState } from '../ui/OptionButton';
import type { ExerciseProps } from '../types';

export default function Choice({ ex, value, onChange, locked, locale }: ExerciseProps<'choice'>) {
  const stateOf = (i: number): OptionState => {
    if (!locked) return value === i ? 'selected' : 'idle';
    if (i === ex.answer) return 'correct';
    if (i === value) return 'wrong';
    return 'idle';
  };

  return (
    <>
      <ExerciseHeading
        instruction={ex.instruction ?? 'Choose the correct translation'}
        prompt={ex.prompt}
        speak={ex.speak}
        locale={locale}
      />
      <div className="grid content-start gap-2.5" role="radiogroup">
        {ex.options.map((option, i) => (
          <OptionButton
            key={i}
            role="radio"
            aria-checked={value === i}
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