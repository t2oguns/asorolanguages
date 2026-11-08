import type { Exercise } from '@/components/features/lesson/types';

export const sampleLesson: Exercise[] = [
  {
    id: 'c1', exercise_type: 'multiple_choice', instruction: 'Choose the correct translation', language: 'es', level: 'A1',
    targets: [], explanation_media: null,
    prompt_blocks: [{ id: 'prompt-1', position: 0, block_type: 'text', text: 'el gato', media: null }],
    options: ['the cat', 'the dog', 'the milk', 'the bird'].map((text, position) => ({ id: String(position), position, text, is_correct: position === 0, media: null })),
    accepted_answers: [], fill_blank_slots: [], matching_pairs: [],
  },
  {
    id: 'i1',
    type: 'intro',
    term: 'el gato',
    translation: 'the cat',
    note: 'Masculine noun, so it takes "el".',
  },
];
