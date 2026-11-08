import { useMemo, useState } from 'react';
import { shuffle } from '@/lib/utils/shuffle';
import OptionButton, { type OptionState } from '../ui/OptionButton';
import Prompt from '../ui/Prompt';
import Media from '../ui/Media';
import type { ExerciseProps } from '../types';

export default function Match({ ex, value, onChange, locked, locale }: ExerciseProps) {
  const matches = typeof value === 'object' && !Array.isArray(value) ? value : {};
  const order = useMemo(() => shuffle(ex.matching_pairs, ex.id), [ex]);
  const [left, setLeft] = useState<string | null>(null);
  const stateOf = (id: string, side: 'left' | 'right'): OptionState => {
    const source = side === 'left' ? id : Object.keys(matches).find((key) => matches[key] === id);
    if (locked && source) return matches[source] === source ? 'correct' : 'wrong';
    if (side === 'left' ? left === id || Boolean(matches[id]) : Object.values(matches).includes(id)) return 'selected';
    return 'idle';
  };
  return <>
    <Prompt ex={ex} locale={locale} />
    <div className="grid grid-cols-2 gap-2 sm:gap-3">
      <div className="grid content-start gap-2.5">{ex.matching_pairs.map((pair) => <div key={pair.id} className="space-y-2">
        <OptionButton aria-pressed={left === pair.id} state={stateOf(pair.id, 'left')} disabled={locked} className={left === pair.id ? 'ring-2 ring-blue-400' : ''} onClick={() => { const next = { ...matches }; delete next[pair.id]; onChange(next); setLeft(pair.id); }}>
          <span aria-hidden="true" className="mr-2 text-sm text-slate-500">{pair.position + 1}</span>{pair.left_text || pair.left_media?.alt_text || 'Left item'}
        </OptionButton><Media asset={pair.left_media} />
      </div>)}</div>
      <div className="grid content-start gap-2.5">{order.map((pair) => <div key={pair.id} className="space-y-2">
        <OptionButton state={stateOf(pair.id, 'right')} disabled={locked || !left || Object.entries(matches).some(([id, right]) => id !== left && right === pair.id)}
          onClick={() => { if (left) { onChange({ ...matches, [left]: pair.id }); setLeft(null); } }}>
          {Object.entries(matches).find(([, right]) => right === pair.id) && <span aria-hidden="true" className="mr-2 text-sm text-slate-500">{(ex.matching_pairs.find((item) => matches[item.id] === pair.id)?.position ?? 0) + 1}</span>}{pair.right_text || pair.right_media?.alt_text || 'Right item'}
        </OptionButton><Media asset={pair.right_media} />
      </div>)}</div>
    </div>
  </>;
}
