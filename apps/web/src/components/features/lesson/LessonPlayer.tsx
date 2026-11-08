'use client';

import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import ExerciseView from './exercises/Index';
import LessonComplete from './exercises/LessonComplete';
import LessonFooter from './LessonFooter';
import LessonHeader from './LessonHeader';
import Media from './ui/Media';
import { correctText, grade } from './lib/answers';
import { startLesson, submitLesson } from './lib/api';
import { isIntro, type BatchResponse, type Exercise, type LessonDelivery, type LessonResult } from './types';
import { column } from './ui/ui';
import { useLesson } from './useLesson';

type PresentationProps = {
  title?: string;
  locale?: string;
  exitHref?: string;
  onComplete?: (result: LessonResult) => void;
};
type Props = PresentationProps & ({ code: string; exercises?: never } | { code?: never; exercises: Exercise[] });

/** Uses the same lesson components for live API delivery and local presentation. */
export default function LessonPlayer(props: Props) {
  if (props.code !== undefined) return <DeliveredLesson {...props} key={props.code} code={props.code} />;
  return <LessonContent {...props} exercises={props.exercises} />;
}

function DeliveredLesson({ code, ...props }: PresentationProps & { code: string }) {
  const [delivery, setDelivery] = useState<LessonDelivery>();
  const [error, setError] = useState('');
  const [visit, setVisit] = useState(0);
  const generation = useRef(0);

  useEffect(() => {
    const current = ++generation.current;
    void startLesson(code).then((data) => {
      if (current === generation.current) setDelivery(data);
    }).catch(() => {
      if (current === generation.current) setError('Could not load this lesson. Reconnect and try again.');
    });
    return () => { generation.current += 1; };
  }, [code, visit]);

  // Next Activity and browser back/forward caching must not restore an attempt.
  useLayoutEffect(() => {
    const discard = () => { generation.current += 1; setDelivery(undefined); setError(''); };
    const returned = (event: PageTransitionEvent) => { if (event.persisted) setVisit((value) => value + 1); };
    window.addEventListener('pagehide', discard);
    window.addEventListener('pageshow', returned);
    return () => {
      window.removeEventListener('pagehide', discard);
      window.removeEventListener('pageshow', returned);
      discard();
    };
  }, []);

  if (!delivery) return <main className={`${column} p-8`} aria-live="polite">
    <p>{error || 'Loading lesson…'}</p>
    {error && <button onClick={() => { setError(''); setVisit((value) => value + 1); }}>Retry loading</button>}
  </main>;
  return <LessonContent {...props} key={delivery.lesson_attempt_id} title={delivery.lesson.title} locale={props.locale ?? delivery.exercises[0]?.language}
    exercises={delivery.exercises} onSubmit={async (responses) => { await submitLesson(code, delivery.lesson_attempt_id, responses); }} />;
}

function LessonContent({ title, exercises, locale = 'es-ES', exitHref = '/dashboard/learn', onComplete, onSubmit }:
  PresentationProps & { exercises: Exercise[]; onSubmit?: (responses: BatchResponse[]) => Promise<void> }) {
  
  const router = useRouter();
  
  const { ex, index, done, answer, setAnswer, status, ready, progress, primary, result, responses, rate } = useLesson(exercises);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const submitting = useRef(false);
  const active = useRef(true);
  const reported = useRef(false);

  useLayoutEffect(() => {
    active.current = true;
    return () => { active.current = false; };
  }, []);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Enter' || event.isComposing || event.target instanceof HTMLButtonElement || event.target instanceof HTMLSelectElement) return;
      event.preventDefault();
      if (!done) primary();
    };
    window.addEventListener('keydown', onKey);
    
    return () => window.removeEventListener('keydown', onKey);
  }, [primary, done]);

  useEffect(() => {
    const beforeUnload = (event: BeforeUnloadEvent) => { if (responses.length) event.preventDefault(); };
    window.addEventListener('beforeunload', beforeUnload);
    
    return () => window.removeEventListener('beforeunload', beforeUnload);
  }, [responses.length]);

  useEffect(() => {
    if (done && !reported.current) { reported.current = true; onComplete?.(result); }
  }, [done, result, onComplete]);

  const leave = () => router.push(exitHref);
  const exit = () => { if ((!responses.length && index === 0) || window.confirm('Leave this lesson? Your progress will be lost.')) leave(); };
  const finish = async () => {
    if (submitting.current) return;
    if (!onSubmit) { leave(); return; }
    submitting.current = true;
    setSaving(true);
    setError('');
    try {
      await onSubmit(responses);
      if (active.current) leave();
    } catch {
      if (active.current) setError('Could not save the lesson. Retry while it is open. Leaving or reloading will lose your answers.');
    } finally {
      submitting.current = false;
      if (active.current) setSaving(false);
    }
  };
  const checkedExercise = ex && !isIntro(ex) && status !== 'answering' ? ex : undefined;
  const evidence = checkedExercise ? grade(checkedExercise, answer).targets : [];
  const ratings = responses.at(-1)?.recall_ratings as Record<string, number> | undefined;

  return <div className="flex min-h-dvh flex-col bg-slate-50 text-slate-900">
    {done || !ex ? <LessonComplete title={title} firstTry={result.firstTryCorrect} total={result.total}
      onFinish={() => void finish()} saving={saving} error={error} /> : <>
      <LessonHeader progress={progress} title={title} onExit={exit} />
      <main className={`${column} flex flex-1 flex-col gap-6 px-5 pt-4 pb-40`} key={`${ex.id}-${index}`}>
        <ExerciseView ex={ex} value={answer} onChange={setAnswer} locked={status !== 'answering'} locale={locale} status={status} />
        {checkedExercise && <section aria-label="Answer explanation" className="space-y-3">
          {checkedExercise.explanation && <p>{checkedExercise.explanation}</p>}
          <Media asset={checkedExercise.explanation_media} />
          {evidence.filter((target) => target.score === 1).map((target) => <label key={target.id} className="block text-sm text-slate-600">
            How well did you remember {target.label}? (Optional)
            <select aria-label={`Recall rating for ${target.label}`} value={ratings?.[String(target.sense_id)] ?? ''}
              onChange={(event) => rate(target.sense_id, event.target.value)} className="ml-2 rounded-lg border bg-white p-2">
              <option value="">Automatic</option><option value="1">Forgot / guessed</option><option value="2">Hard</option><option value="3">Good</option><option value="4">Easy</option>
            </select>
          </label>)}
        </section>}
      </main>
      <LessonFooter status={status} ready={ready} label={status === 'answering' && !isIntro(ex) ? 'Check' : 'Continue'}
        wrongTitle={!isIntro(ex) && ex.exercise_type === 'matching' ? 'Review these pairs' : 'Correct answer'} detail={correctText(ex)} onPrimary={primary} />
    </>}
  </div>;
}
