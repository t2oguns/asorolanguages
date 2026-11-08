import { useMemo } from 'react';
import { shuffle } from '@/lib/utils/shuffle';
import { wordTiles } from '../lib/answers';
import WordTile from '../ui/WordTile';
import Prompt from '../ui/Prompt';
import type { ExerciseProps } from '../types';

export default function WordBank({ ex, value, onChange, locked, locale }: ExerciseProps) {
  const picked = Array.isArray(value) ? value : [];
  const words = useMemo(() => shuffle(wordTiles(ex), ex.id), [ex]);
  return <>
    <Prompt ex={ex} locale={locale} />
    <div className="flex min-h-16 flex-wrap items-start gap-2 border-y-2 border-slate-200 py-2" role="group" aria-label="Your answer">
      {picked.map((word, index) => <WordTile key={index} disabled={locked}
        onClick={() => onChange(picked.filter((_, position) => position !== index))}>{word}</WordTile>)}
    </div>
    <div className="flex flex-wrap justify-center gap-2" role="group" aria-label="Word bank">
      {words.map((word, index) => {
        const used = picked.filter((item) => item === word).length >= words.slice(0, index + 1).filter((item) => item === word).length;
        return <WordTile key={index} used={used} disabled={locked || used} onClick={() => onChange([...picked, word])}>{word}</WordTile>;
      })}
    </div>
  </>;
}
