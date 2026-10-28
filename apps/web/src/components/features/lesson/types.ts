export type Exercise =
  // A new word or phrase shown before it's tested. Not scored.
  | {
      id: string;
      type: 'intro';
      term: string;
      translation: string;
      note?: string;
      speak?: string;
    }
  // Pick the right option from a list.
  | {
      id: string;
      type: 'choice';
      instruction?: string;
      prompt: string;
      options: string[];
      answer: number; // index into options
      speak?: string;
    }
  // Build a sentence by tapping words. `words` is the bank in display order,
  // so include any distractors and shuffle them yourself.
  | {
      id: string;
      type: 'wordbank';
      instruction?: string;
      prompt: string;
      words: string[];
      answer: string[];
      alternatives?: string[][]; // other accepted orderings
      speak?: string;
    }
  // Complete a sentence with the missing word.
  | {
      id: string;
      type: 'fill';
      instruction?: string;
      before: string;
      after: string;
      options: string[];
      answer: number;
      translation?: string;
    }
  // Type the answer.
  | {
      id: string;
      type: 'type';
      instruction?: string;
      prompt: string;
      accepted: string[]; // first entry is shown as the correct answer
      speak?: string;
    }
  // Match each term on the left with its pair on the right.
  | {
      id: string;
      type: 'match';
      instruction?: string;
      pairs: { left: string; right: string }[];
    };
 
export type LessonResult = {
  total: number; // scored exercises (intro cards excluded)
  firstTryCorrect: number;
  missedIds: string[];
  accuracy: number; // 0 to 1
};
 
/* ---------- internal lesson state ---------- */
 
export type MatchState = { matched: number[]; mistakes: number };
export type Answer = number | number[] | string | MatchState | null;
export type Status = 'answering' | 'correct' | 'wrong';
 
export type Of<T extends Exercise['type']> = Extract<Exercise, { type: T }>;
 
export type ExerciseCommonProps = {
  value: Answer;
  onChange: (a: Answer) => void;
  locked: boolean;
  locale: string;
  status: Status;
};
 
export type ExerciseProps<T extends Exercise['type']> = ExerciseCommonProps & {
  ex: Of<T>;
};