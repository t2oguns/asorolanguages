import type { Answer, Exercise, MatchState } from '../types';

export function initialAnswer(ex: Exercise | undefined): Answer {
  if (!ex) return null;
  switch (ex.type) {
    case 'wordbank':
      return [];
    case 'type':
      return '';
    case 'match':
      return { matched: [], mistakes: 0 };
    default:
      return null;
  }
}

export function norm(s: string, stripAccents: boolean) {
  let t = s
    .trim()
    .toLowerCase()
    .replace(/[.,!?¿¡;:"“”]/g, '')
    .replace(/\s+/g, ' ');
  if (stripAccents) t = t.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  return t;
}

/** Can the learner press Check yet? */
export function isReady(ex: Exercise, a: Answer): boolean {
  switch (ex.type) {
    case 'intro':
      return true;
    case 'choice':
    case 'fill':
      return typeof a === 'number';
    case 'wordbank':
      return Array.isArray(a) && a.length > 0;
    case 'type':
      return typeof a === 'string' && a.trim().length > 0;
    case 'match':
      return (a as MatchState).matched.length === ex.pairs.length;
  }
}

export function isCorrect(ex: Exercise, a: Answer, ignoreAccents: boolean): boolean {
  switch (ex.type) {
    case 'intro':
      return true;
    case 'choice':
    case 'fill':
      return a === ex.answer;
    case 'wordbank': {
      const given = (a as number[]).map((i) => ex.words[i]).join(' ');
      return [ex.answer, ...(ex.alternatives ?? [])].some(
        (c) => norm(c.join(' '), ignoreAccents) === norm(given, ignoreAccents),
      );
    }
    case 'type':
      return ex.accepted.some(
        (c) => norm(c, ignoreAccents) === norm(a as string, ignoreAccents),
      );
    case 'match':
      return (a as MatchState).mistakes === 0;
  }
}

/** Text shown in the feedback bar after a wrong answer. */
export function correctText(ex: Exercise): string {
  switch (ex.type) {
    case 'choice':
      return ex.options[ex.answer];
    case 'fill':
      return `${ex.before} ${ex.options[ex.answer]} ${ex.after}`.replace(/\s+/g, ' ').trim();
    case 'wordbank':
      return ex.answer.join(' ');
    case 'type':
      return ex.accepted[0];
    case 'match':
      return ex.pairs.map((p) => `${p.left} = ${p.right}`).join(', ');
    default:
      return '';
  }
}