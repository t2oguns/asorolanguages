import { useCallback, useMemo, useRef, useState } from 'react';
import { initialAnswer, isCorrect, isReady } from './lib/answers';
import type { Answer, Exercise, LessonResult, Status } from './types';

/**
 * Owns the lesson's state: the exercise queue, the current answer, and
 * whether it has been checked. Missed exercises are re-queued once.
 */
export function useLesson(exercises: Exercise[], ignoreAccents: boolean) {
  const [queue, setQueue] = useState<Exercise[]>(exercises);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState<Answer>(() => initialAnswer(exercises[0]));
  const [status, setStatus] = useState<Status>('answering');
  const [firstTry, setFirstTry] = useState(0);
  const [missedIds, setMissedIds] = useState<string[]>([]);

  const attempted = useRef(new Set<string>());

  const total = useMemo(() => exercises.filter((e) => e.type !== 'intro').length, [exercises]);
  const done = index >= queue.length;
  const ex: Exercise | undefined = queue[index];

  const next = useCallback(() => {
    const nextIndex = index + 1;
    setIndex(nextIndex);
    setStatus('answering');
    setAnswer(initialAnswer(queue[nextIndex]));
  }, [index, queue]);

  const check = useCallback(() => {
    if (!ex || status !== 'answering' || !isReady(ex, answer)) return;
    if (ex.type === 'intro') {
      next();
      return;
    }
    const ok = isCorrect(ex, answer, ignoreAccents);
    const first = !attempted.current.has(ex.id);
    attempted.current.add(ex.id);
    if (ok && first) setFirstTry((n) => n + 1);
    if (!ok && first) {
      setMissedIds((ids) => [...ids, ex.id]);
      setQueue((q) => [...q, ex]); // comes back once at the end
    }
    setStatus(ok ? 'correct' : 'wrong');
  }, [ex, status, answer, ignoreAccents, next]);

  const result: LessonResult = {
    total,
    firstTryCorrect: firstTry,
    missedIds,
    accuracy: total ? firstTry / total : 1,
  };

  return {
    ex,
    index,
    done,
    answer,
    setAnswer,
    status,
    ready: ex ? isReady(ex, answer) : false,
    progress: queue.length ? (index / queue.length) * 100 : 100,
    check,
    next,
    primary: status === 'answering' ? check : next,
    result,
  };
}