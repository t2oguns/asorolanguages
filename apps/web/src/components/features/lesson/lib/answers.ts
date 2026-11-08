import overrides from './casefold.json';
import { isIntro, type Answer, type Exercise, type GradedExercise, type Evidence, type Policy } from '../types';

const casefold = overrides as Record<string, string>;
export function normalize(text: string, policy: Policy) {
  let value = text.normalize('NFC');
  if (!policy.case_sensitive) value = Array.from(value, (char) => casefold[char] ?? char.toLowerCase()).join('');
  if (policy.ignore_diacritics) value = value.normalize('NFD').replace(/\p{Mn}/gu, '');
  if (policy.ignore_punctuation) value = value.replace(/\p{P}/gu, '');
  return value.normalize('NFC').replace(/[\p{White_Space}\u001c-\u001f]+/gu, ' ').replace(/^ | $/g, '');
}
const sameSet = (a: string[], b: string[]) => a.length === b.length && new Set(a).size === a.length && a.every((id) => b.includes(id));
const sameMultiset = (a: string[], b: string[]) => JSON.stringify([...a].sort()) === JSON.stringify([...b].sort());
const record = (answer: Answer): answer is Record<string, string> => typeof answer === 'object' && answer !== null && !Array.isArray(answer);
export function acceptedAnswers(exercise: GradedExercise) {
  return [...exercise.accepted_answers].sort((a, b) => Number(Boolean(b.is_primary)) - Number(Boolean(a.is_primary)) || a.id.localeCompare(b.id));
}
export const wordTiles = (exercise: GradedExercise) => acceptedAnswers(exercise)[0]?.text.split(/[\p{White_Space}\u001c-\u001f]+/u).filter(Boolean) ?? [];
export function initialAnswer(exercise?: Exercise): Answer {
  if (!exercise || isIntro(exercise)) return '';
  if (['multiple_choice', 'word_order'].includes(exercise.exercise_type)) return [];
  if (['matching', 'fill_blank'].includes(exercise.exercise_type)) return {};
  return '';
}
export function isReady(exercise: Exercise, answer: Answer) {
  if (isIntro(exercise)) return true;
  switch (exercise.exercise_type) {
    case 'multiple_choice': return Array.isArray(answer) && answer.length > 0;
    case 'word_order': return Array.isArray(answer) && answer.length === wordTiles(exercise).length;
    case 'fill_blank': return record(answer) && exercise.fill_blank_slots.every((row) => Boolean(answer[row.id]?.trim()));
    case 'matching': return record(answer) && exercise.matching_pairs.every((row) => Boolean(answer[row.id])) && new Set(Object.values(answer)).size === Object.keys(answer).length;
    default: return typeof answer === 'string' && Boolean(answer.trim());
  }
}
export function grade(exercise: GradedExercise, answer: Answer): { score: number; targets: Evidence[] } {
  const textScore = (value: string, answers: string[]) => Number(answers.some((accepted) => normalize(accepted, exercise) === normalize(value, exercise)));
  const evidence: Record<string, number[]> = {};
  let score: number;
  switch (exercise.exercise_type) {
    case 'multiple_choice':
      if (!Array.isArray(answer) || new Set(answer).size !== answer.length || !answer.every((id) => exercise.options.some((row) => row.id === id))) throw new Error('Choose valid options.');
      score = Number(sameSet(answer, exercise.options.filter((row) => row.is_correct).map((row) => row.id)));
      break;
    case 'word_order':
      if (!Array.isArray(answer) || !sameMultiset(answer, wordTiles(exercise))) throw new Error('Use each word tile once.');
      score = textScore(answer.join(' '), acceptedAnswers(exercise).map((row) => row.text));
      break;
    case 'fill_blank':
    case 'matching': {
      const rows = exercise.exercise_type === 'fill_blank' ? exercise.fill_blank_slots : exercise.matching_pairs;
      if (!record(answer) || !sameSet(Object.keys(answer), rows.map((row) => row.id))) throw new Error('Answer each item.');
      if (exercise.exercise_type === 'matching' && !sameSet(Object.values(answer), rows.map((row) => row.id))) throw new Error('Match each item once.');
      const scores = rows.map((row) => {
        const value = 'accepted_answers' in row ? textScore(answer[row.id], row.accepted_answers.map((item) => item.text)) : Number(answer[row.id] === row.id);
        (evidence[row.target_id ?? exercise.targets[0].id] ??= []).push(value);
        return value;
      });
      score = scores.reduce((sum, value) => sum + value, 0) / scores.length;
      break;
    }
    default:
      if (typeof answer !== 'string') throw new Error('Enter a text answer.');
      score = textScore(answer, acceptedAnswers(exercise).map((row) => row.text));
  }
  return { score, targets: exercise.targets.flatMap((target) => {
    const values = ['matching', 'fill_blank'].includes(exercise.exercise_type) ? evidence[target.id] ?? [] : [score];
    return values.length ? [{ ...target, score: values.reduce((sum, value) => sum + value, 0) / values.length }] : [];
  }) };
}

/** Corrections shown by the existing feedback footer after checking. */
export function correctText(exercise: Exercise): string {
  if (isIntro(exercise)) return '';
  switch (exercise.exercise_type) {
    case 'multiple_choice': return exercise.options.filter((row) => row.is_correct).map((row) => row.text || row.media?.alt_text || 'Media answer').join(', ');
    case 'fill_blank': return exercise.fill_blank_slots.map((row) => row.accepted_answers.map((answer) => answer.text).join(' / ')).join('; ');
    case 'matching': return exercise.matching_pairs.map((row) => `${row.left_text || row.left_media?.alt_text || 'Media'} = ${row.right_text || row.right_media?.alt_text || 'Media'}`).join(', ');
    default: return acceptedAnswers(exercise).map((row) => row.text).join(' / ');
  }
}
