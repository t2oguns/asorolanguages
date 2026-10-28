import type { Exercise, ExerciseCommonProps } from '../types';
import Choice from './Choice';
import Fill from './Fill';
import Intro from './Intro';
import Match from './Match';
import TypeIn from './TypeIn';
import WordBank from './WordBank';
 
/** Renders the right component for an exercise's `type`. */
export default function ExerciseView({ ex, ...rest }: { ex: Exercise } & ExerciseCommonProps) {
  switch (ex.type) {
    case 'intro':
      return <Intro ex={ex} {...rest} />;
    case 'choice':
      return <Choice ex={ex} {...rest} />;
    case 'wordbank':
      return <WordBank ex={ex} {...rest} />;
    case 'fill':
      return <Fill ex={ex} {...rest} />;
    case 'type':
      return <TypeIn ex={ex} {...rest} />;
    case 'match':
      return <Match ex={ex} {...rest} />;
  }
}
 