import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { Exercise } from './types';
import { useLesson } from './useLesson';
 
const intro: Exercise = { id: 'i1', type: 'intro', term: 'hola', translation: 'hello' };
const choice: Exercise = { id: 'c1', type: 'choice', prompt: 'x', options: ['a', 'b'], answer: 0 };
const typed: Exercise = { id: 't1', type: 'type', prompt: 'y', accepted: ['hola'] };
 
describe('useLesson', () => {
  it('starts on the first exercise with no progress', () => {
    const { result } = renderHook(() => useLesson([intro, choice], true));
    expect(result.current.ex?.id).toBe('i1');
    expect(result.current.progress).toBe(0);
    expect(result.current.done).toBe(false);
    expect(result.current.status).toBe('answering');
  });
 
  it('moves past an intro card without scoring it', () => {
    const { result } = renderHook(() => useLesson([intro, choice], true));
    act(() => result.current.check());
    expect(result.current.ex?.id).toBe('c1');
    expect(result.current.result.total).toBe(1);
    expect(result.current.result.firstTryCorrect).toBe(0);
  });
 
  it('ignores check until an answer is ready', () => {
    const { result } = renderHook(() => useLesson([choice], true));
    expect(result.current.ready).toBe(false);
    act(() => result.current.check());
    expect(result.current.status).toBe('answering');
  });
 
  it('counts a first-try correct answer', () => {
    const { result } = renderHook(() => useLesson([choice], true));
    act(() => result.current.setAnswer(0));
    act(() => result.current.check());
    expect(result.current.status).toBe('correct');
    expect(result.current.result.firstTryCorrect).toBe(1);
    act(() => result.current.next());
    expect(result.current.done).toBe(true);
    expect(result.current.result.accuracy).toBe(1);
  });
 
  it('re-queues a missed exercise once and does not score the retry', () => {
    const { result } = renderHook(() => useLesson([choice], true));
 
    act(() => result.current.setAnswer(1));
    act(() => result.current.check());
    expect(result.current.status).toBe('wrong');
    expect(result.current.result.missedIds).toEqual(['c1']);
 
    act(() => result.current.next());
    expect(result.current.ex?.id).toBe('c1'); // came back
    expect(result.current.answer).toBeNull(); // fresh state
 
    act(() => result.current.setAnswer(0));
    act(() => result.current.check());
    expect(result.current.status).toBe('correct');
    act(() => result.current.next());
 
    expect(result.current.done).toBe(true);
    expect(result.current.result).toEqual({
      total: 1,
      firstTryCorrect: 0,
      missedIds: ['c1'],
      accuracy: 0,
    });
  });
 
  it('does not re-queue a second miss of the same exercise', () => {
    const { result } = renderHook(() => useLesson([choice], true));
    for (let i = 0; i < 2; i++) {
      act(() => result.current.setAnswer(1));
      act(() => result.current.check());
      act(() => result.current.next());
    }
    expect(result.current.done).toBe(true);
    expect(result.current.result.missedIds).toEqual(['c1']);
  });
 
  it('reports progress as a percentage of the queue', () => {
    const { result } = renderHook(() => useLesson([choice, typed], true));
    act(() => result.current.setAnswer(0));
    act(() => result.current.check());
    act(() => result.current.next());
    expect(result.current.progress).toBe(50);
  });
 
  it('primary() checks first, then continues', () => {
    const { result } = renderHook(() => useLesson([choice, typed], true));
    act(() => result.current.setAnswer(0));
    act(() => result.current.primary()); // check
    expect(result.current.status).toBe('correct');
    act(() => result.current.primary()); // next
    expect(result.current.ex?.id).toBe('t1');
    expect(result.current.status).toBe('answering');
  });
})