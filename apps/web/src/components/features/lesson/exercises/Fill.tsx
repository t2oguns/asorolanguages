import ExerciseHeading from '../ui/ExerciseHeading';
import Media from '../ui/Media';
import type { ExerciseProps } from '../types';

export default function Fill({ ex, value, onChange, locked, locale }: ExerciseProps) {
  const answers = typeof value === 'object' && !Array.isArray(value) ? value : {};
  return <>
    <ExerciseHeading instruction={ex.instruction} locale={locale} />
    {ex.prompt_blocks.map((block) => {
      const text = Array.from(block.text);
      const slots = ex.fill_blank_slots.filter((slot) => slot.source_block_id === block.id).sort((a, b) => a.start_offset - b.start_offset);
      let cursor = 0;
      return <div key={block.id} className="text-[clamp(1.4rem,3.6vw,1.8rem)] font-semibold leading-relaxed">
        {block.media ? <Media asset={block.media} /> : <>{slots.map((slot, index) => {
          const prefix = text.slice(cursor, slot.start_offset).join('');
          cursor = slot.end_offset;
          return <span key={slot.id}>{prefix}<input aria-label={`Blank ${block.position + 1}.${index + 1}`} value={answers[slot.id] ?? ''}
            onChange={(event) => onChange({ ...answers, [slot.id]: event.target.value })} disabled={locked} autoComplete="off"
            className="mx-1 inline-block w-32 border-b-[3px] border-slate-200 bg-transparent px-2 text-center text-blue-600 focus:border-blue-600 focus:outline-none" /></span>;
        })}{text.slice(cursor).join('')}</>}
      </div>;
    })}
  </>;
}
