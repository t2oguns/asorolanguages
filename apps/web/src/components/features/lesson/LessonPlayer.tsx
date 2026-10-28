'use client';

import { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import ExerciseView from './exercises/Index';
import LessonComplete from './exercises/LessonComplete';
import LessonFooter from './LessonFooter';
import LessonHeader from './LessonHeader';
import { correctText } from './lib/answers';
import type { Exercise, LessonResult } from './types';
import { column } from './ui/ui';
import { useLesson } from './useLesson';

type Props = {
  title?: string;
  exercises: Exercise[];
  /** BCP 47 locale of the language being learned, used for text-to-speech. */
  locale?: string;
  /** Treat "cafe" and "café" as the same answer when typing. */
  ignoreAccents?: boolean;
  exitHref?: string;
  /** Only usable if the parent is a client component. */
  onComplete?: (result: LessonResult) => void;
};

export default function LessonPlayer({
  title,
  exercises,
  locale = 'es-ES',
  ignoreAccents = true,
  exitHref = '/dashboard/learn',
  onComplete,
}: Props) {
  const router = useRouter();
  const { ex, index, done, answer, setAnswer, status, ready, progress, primary, result } = 
    useLesson(exercises, ignoreAccents);

  // Enter checks / continues. Ignore it when a button has focus: the browser
  // already turns Enter into a click there.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Enter' || e.target instanceof HTMLButtonElement) return;
      e.preventDefault();
      if (!done) primary();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [primary, done]);

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  const reported = useRef(false);
  
  useEffect(() => {
    if (done && !reported.current) {
      reported.current = true;
      onComplete?.(result);
    }
  }, [done, result, onComplete]);

  const leave = () => router.push(exitHref);
  const exit = () => {
    if (index === 0 || window.confirm('Leave this lesson? Your progress will be lost.')) leave();
  };

  return (
    <div className="flex min-h-dvh flex-col bg-slate-50 text-slate-900">
      {done || !ex ? (
        <LessonComplete
          title={title}
          firstTry={result.firstTryCorrect}
          total={result.total}
          onFinish={leave}
        />
      ) : (
        <>
          <LessonHeader progress={progress} title={title} onExit={exit} />

          <main className={`${column} flex flex-1 flex-col gap-6 px-5 pt-4 pb-40`} key={`${ex.id}-${index}`}>
            <ExerciseView
              ex={ex}
              value={answer}
              onChange={setAnswer}
              locked={status !== 'answering'}
              locale={locale}
              status={status}
            />
          </main>

          <LessonFooter
            status={status}
            ready={ready}
            label={status === 'answering' && ex.type !== 'intro' ? 'Check' : 'Continue'}
            wrongTitle={ex.type === 'match' ? 'Review these pairs' : 'Correct answer'}
            detail={correctText(ex)}
            onPrimary={primary}
          />
        </>
      )}
    </div>
  );
}