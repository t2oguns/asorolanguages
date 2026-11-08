import { useCallback, useRef, useState } from 'react';
import { grade, initialAnswer, isReady } from './lib/answers';
import { isIntro, type Answer, type BatchResponse, type Exercise, type LessonResult, type Status } from './types';

/** Check / Continue, one practice requeue, and an in-memory final answer batch. */
export function useLesson(exercises: Exercise[]) {
  const [queue, setQueue] = useState(exercises);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState<Answer>(() => initialAnswer(exercises[0]));
  const [status, setStatus] = useState<Status>('answering');
  const [firstTry, setFirstTry] = useState(0);
  const [missedIds, setMissedIds] = useState<string[]>([]);
  const [responses, setResponses] = useState<BatchResponse[]>([]);
  const attempted = useRef(new Set<string>());
  const total = exercises.filter((exercise) => !isIntro(exercise)).length;
  const done = index >= queue.length;
  const ex = queue[index] as Exercise | undefined;

  const next = useCallback(() => {
    setIndex(index + 1);
    setStatus('answering');
    setAnswer(initialAnswer(queue[index + 1]));
  }, [index, queue]);
  const check = useCallback(() => {
    if (!ex || status !== 'answering' || !isReady(ex, answer)) return;
    if (isIntro(ex)) { next(); return; }
    const score = grade(ex, answer).score;
    const first = !attempted.current.has(ex.id);
    attempted.current.add(ex.id);
    if (score === 1 && first) setFirstTry((value) => value + 1);
    if (score < 1 && first) {
      setMissedIds((ids) => [...ids, ex.id]);
      setQueue((items) => [...items, ex]);
    }
    setResponses((items) => [...items, { exercise_id: ex.id, response: answer }]);
    setStatus(score === 1 ? 'correct' : 'wrong');
  }, [ex, status, answer, next]);
  const rate = (senseId: number, rating: string) => setResponses((items) => items.map((item, index) => {
    if (index !== items.length - 1) return item;
    const ratings = { ...(item.recall_ratings as Record<string, number> | undefined) };
    if (rating) ratings[String(senseId)] = Number(rating); else delete ratings[String(senseId)];
    return { ...item, recall_ratings: ratings };
  }));
  const result: LessonResult = { total, firstTryCorrect: firstTry, missedIds, accuracy: total ? firstTry / total : 1 };
  return { ex, index, done, answer, setAnswer, status, ready: ex ? isReady(ex, answer) : false,
    progress: queue.length ? index / queue.length * 100 : 100, check, next,
    primary: status === 'answering' ? check : next, result, responses, rate };
}
