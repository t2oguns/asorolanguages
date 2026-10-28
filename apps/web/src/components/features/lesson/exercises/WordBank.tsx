import WordTile from '../ui/WordTile';
import ExerciseHeading from '../ui/ExerciseHeading';
import type { ExerciseProps } from '../types';

export default function WordBank({ ex, value, onChange, locked, locale }: ExerciseProps<'wordbank'>) {
  const picked = value as number[];

  return (
    <>
      <ExerciseHeading
        instruction={ex.instruction ?? 'Translate this sentence'}
        prompt={ex.prompt}
        speak={ex.speak}
        locale={locale}
      />

      <div
        className="flex min-h-16 flex-wrap items-start gap-2 border-y-2 border-slate-200 py-2"
        aria-label="Your answer"
      >
        {picked.map((i) => (
          <WordTile
            key={i}
            disabled={locked}
            onClick={() => onChange(picked.filter((x) => x !== i))}
          >
            {ex.words[i]}
          </WordTile>
        ))}
      </div>

      <div className="flex flex-wrap justify-center gap-2">
        {ex.words.map((word, i) => (
          <WordTile
            key={i}
            used={picked.includes(i)}
            disabled={locked || picked.includes(i)}
            onClick={() => onChange([...picked, i])}
          >
            {word}
          </WordTile>
        ))}
      </div>
    </>
  );
}