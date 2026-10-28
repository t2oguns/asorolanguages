import { useEffect, useState } from 'react';
import ExerciseHeading from '../ui/ExerciseHeading';
import OptionButton, { type OptionState } from '../ui/OptionButton';
import type { ExerciseProps, MatchState } from '../types';
import { shuffle } from '@/lib/utils/shuffle';

export default function Match({ ex, value, onChange, locked }: ExerciseProps<'match'>) {
  const state = value as MatchState;
  const [order, setOrder] = useState(() => ex.pairs.map((_, i) => i));
  const [left, setLeft] = useState<number | null>(null);
  const [right, setRight] = useState<number | null>(null);
  const [flash, setFlash] = useState(false);

  // Shuffle after mount so server and client markup agree during hydration.
  useEffect(() => {
    setOrder((o) => shuffle(o));
  }, []);

  const pick = (side: 'l' | 'r', i: number) => {
    if (locked || flash || state.matched.includes(i)) return;
    const l = side === 'l' ? i : left;
    const r = side === 'r' ? i : right;
    if (side === 'l') setLeft(i);
    else setRight(i);
    if (l === null || r === null) return;

    if (l === r) {
      onChange({ matched: [...state.matched, l], mistakes: state.mistakes });
      setLeft(null);
      setRight(null);
    } else {
      onChange({ ...state, mistakes: state.mistakes + 1 });
      setFlash(true);
      setTimeout(() => {
        setFlash(false);
        setLeft(null);
        setRight(null);
      }, 600);
    }
  };

  const stateOf = (side: 'l' | 'r', i: number): OptionState => {
    if (state.matched.includes(i)) return 'correct';
    const selected = side === 'l' ? left === i : right === i;
    if (!selected) return 'idle';
    return flash ? 'wrong' : 'selected';
  };

  return (
    <>
      <ExerciseHeading instruction={ex.instruction ?? 'Tap the matching pairs'} />
      <div className="grid grid-cols-2 gap-2 sm:gap-3">
        <div className="grid content-start gap-2.5">
          {ex.pairs.map((p, i) => (
            <OptionButton
              key={i}
              state={stateOf('l', i)}
              disabled={locked || state.matched.includes(i)}
              onClick={() => pick('l', i)}
            >
              {p.left}
            </OptionButton>
          ))}
        </div>
        <div className="grid content-start gap-2.5">
          {order.map((i) => (
            <OptionButton
              key={i}
              state={stateOf('r', i)}
              disabled={locked || state.matched.includes(i)}
              onClick={() => pick('r', i)}
            >
              {ex.pairs[i].right}
            </OptionButton>
          ))}
        </div>
      </div>
    </>
  );
}