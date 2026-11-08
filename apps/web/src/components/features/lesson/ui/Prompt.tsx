import type { GradedExercise } from '../types';
import ExerciseHeading from './ExerciseHeading';
import Media from './Media';
import AudioButton from './AudioButton';

export default function Prompt({ ex, locale }: { ex: GradedExercise; locale: string }) {
  return <>
    <ExerciseHeading instruction={ex.instruction} locale={locale} />
    {ex.prompt_blocks.map((block) => <div key={block.id} className="text-[clamp(1.4rem,3.6vw,1.8rem)] font-semibold leading-relaxed">
      {block.media ? <Media asset={block.media} /> : <span className="flex items-center gap-3">{['word', 'expression'].includes(block.block_type) && <AudioButton text={block.text} locale={locale} />}{block.text}</span>}
    </div>)}
  </>;
}
