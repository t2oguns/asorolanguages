import { expect, it } from 'vitest';
import cases from '../../../../../../../shared/grading-normalization.json';
import gradingCases from '../../../../../../../shared/grading-cases.json';
import { grade, normalize } from './answers';
import type { Answer, GradedExercise, Policy } from '../types';
const policy: Policy = { case_sensitive: false, ignore_punctuation: false, ignore_diacritics: false };
for (const example of cases) it(`normalizes ${JSON.stringify(example.text)}`, () => {
  expect(normalize(example.text, { ...policy, ...example.policy })).toBe(example.expected);
});
for (const example of gradingCases) it(example.name, () => {
  const result = grade(example.exercise as GradedExercise, example.response as Answer);
  expect(result.score).toBeCloseTo(example.score);
  result.targets.forEach((target, index) => expect(target.score).toBeCloseTo(example.target_scores[index]));
});
