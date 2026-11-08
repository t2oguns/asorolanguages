import { isIntro, type Exercise, type ExerciseCommonProps } from '../types';
import Choice from './Choice';
import Fill from './Fill';
import Intro from './Intro';
import Match from './Match';
import TypeIn from './TypeIn';
import WordBank from './WordBank';

export default function ExerciseView({ ex, ...rest }: { ex: Exercise } & ExerciseCommonProps) {
  if (isIntro(ex)) return <Intro ex={ex} {...rest} />;
  switch (ex.exercise_type) {
    case 'multiple_choice': return <Choice ex={ex} {...rest} />;
    case 'word_order': return <WordBank ex={ex} {...rest} />;
    case 'fill_blank': return <Fill ex={ex} {...rest} />;
    case 'translation':
    case 'error_correction': return <TypeIn ex={ex} {...rest} />;
    case 'matching': return <Match ex={ex} {...rest} />;
  }
}
