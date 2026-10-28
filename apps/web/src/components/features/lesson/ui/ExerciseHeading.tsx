import AudioButton from './AudioButton';
 
type Props = {
  instruction?: string;
  prompt?: string;
  speak?: string;
  locale?: string;
};
 
export default function ExerciseHeading({ instruction, prompt, speak, locale = '' }: Props) {
  return (
    <div className="flex flex-col gap-2.5">
      {instruction && <p className="text-[0.95rem] font-semibold text-slate-500">{instruction}</p>}
      {prompt && (
        <p className="flex items-center gap-3 text-[clamp(1.5rem,4vw,2rem)] font-bold leading-tight">
          <AudioButton text={speak} locale={locale} />
          <span>{prompt}</span>
        </p>
      )}
    </div>
  );
}
 