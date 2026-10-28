import type { Exercise } from '@/components/features/lesson/types';

export const sampleLesson: Exercise[] = [
  {
    id: 'c1',
    type: 'choice',
    prompt: 'el gato',
    options: ['the cat', 'the dog', 'the milk', 'the bird'],
    answer: 0,
  },
  {
    id: 'i1',
    type: 'intro',
    term: 'el gato',
    translation: 'the cat',
    note: 'Masculine noun, so it takes "el".',
  },
  /*{
    id: 'i2',
    type: 'intro',
    term: 'la leche',
    translation: 'the milk',
    note: 'Feminine noun, so it takes "la".',
  },
  {
    id: 'm1',
    type: 'match',
    pairs: [
      { left: 'gato', right: 'cat' },
      { left: 'leche', right: 'milk' },
      { left: 'perro', right: 'dog' },
      { left: 'casa', right: 'house' },
    ],
  },
  {
    id: 'w1',
    type: 'wordbank',
    prompt: 'The cat drinks milk',
    words: ['gato', 'El', 'leche', 'la', 'bebe', 'perro'],
    answer: ['El', 'gato', 'bebe', 'leche'],
  },
  {
    id: 'f1',
    type: 'fill',
    before: 'Yo bebo',
    after: 'todos los días.',
    options: ['leche', 'gato', 'casa'],
    answer: 0,
    translation: 'I drink milk every day.',
  },
  {
    id: 't1',
    type: 'type',
    prompt: 'the milk',
    accepted: ['la leche', 'leche'],
  },*/
];