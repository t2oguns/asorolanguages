import OptionButton, { type OptionState } from '../ui/OptionButton';
import Prompt from '../ui/Prompt';
import Media from '../ui/Media';
import type { ExerciseProps } from '../types';

export default function Choice({ ex, value, onChange, locked, locale }: ExerciseProps) {
  const selected = Array.isArray(value) ? value : [];
  const multiple = ex.options.filter((row) => row.is_correct).length > 1;
  const stateOf = (id: string, correct: boolean): OptionState => {
    if (!locked) return selected.includes(id) ? 'selected' : 'idle';
    if (correct) return 'correct';
    return selected.includes(id) ? 'wrong' : 'idle';
  };
  return <>
    <Prompt ex={ex} locale={locale} />
    {multiple && <p className="text-sm text-slate-500">Select all answers that apply</p>}
    <div className="grid content-start gap-2.5" role={multiple ? 'group' : 'radiogroup'}>
      {ex.options.map((option, index) => <div key={option.id} className="space-y-2">
        <OptionButton role={multiple ? 'checkbox' : 'radio'} aria-checked={selected.includes(option.id)}
          state={stateOf(option.id, Boolean(option.is_correct))} disabled={locked}
          onClick={() => onChange(multiple ? selected.includes(option.id) ? selected.filter((id) => id !== option.id) : [...selected, option.id] : [option.id])}>
          {option.text || option.media?.alt_text || `Option ${index + 1}`}
        </OptionButton>
        <Media asset={option.media} />
      </div>)}
    </div>
  </>;
}
