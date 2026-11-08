import type { GradedExercise } from '../types';

export function exerciseFixture(overrides: Partial<GradedExercise> = {}): GradedExercise {
  return {
    id: '00000000-0000-4000-8000-000000000002', exercise_type: 'multiple_choice', instruction: 'Choose the correct translation', language: 'es', level: 'A1',
    case_sensitive: false, ignore_diacritics: false, ignore_punctuation: false, explanation: '', explanation_media: null,
    targets: [{ id: 'target-1', sense_id: 42, lexeme_id: 'lexeme-1', label: 'hola', meaning: 'hello' }],
    prompt_blocks: [{ id: 'block-1', position: 0, block_type: 'text', text: 'el gato', media: null }],
    options: [{ id: 'yes', position: 0, text: 'the cat', is_correct: true, media: null }, { id: 'no', position: 1, text: 'the dog', is_correct: false, media: null }],
    accepted_answers: [], fill_blank_slots: [], matching_pairs: [], ...overrides,
  };
}
