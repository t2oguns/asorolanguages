import type { components } from '@/lib/api/api-schema';

// API contracts come from `npm run api:types`, never a second handwritten DTO.
export type GradedExercise = components['schemas']['Exercise'];
export type LessonDelivery = components['schemas']['LessonSessionPayload'];
export type BatchResponse = components['schemas']['LessonResponse'];
export type Receipt = components['schemas']['SubmissionReceipt'];
export type Media = components['schemas']['Media'];
export type Policy = Pick<GradedExercise, 'case_sensitive' | 'ignore_punctuation' | 'ignore_diacritics'>;
export type Evidence = components['schemas']['Target'] & { score: number };

// Intro cards and the following types describe local presentation/state only.
export type IntroCard = { id: string; type: 'intro'; term: string; translation: string; note?: string; speak?: string };
export type Exercise = GradedExercise | IntroCard;
export const isIntro = (exercise: Exercise): exercise is IntroCard => 'type' in exercise;
export type Answer = string | string[] | Record<string, string>;
export type Status = 'answering' | 'correct' | 'wrong';
export type LessonResult = { total: number; firstTryCorrect: number; missedIds: string[]; accuracy: number };
export type ExerciseCommonProps = { value: Answer; onChange: (answer: Answer) => void; locked: boolean; locale: string; status: Status };
export type ExerciseProps = ExerciseCommonProps & { ex: GradedExercise };
