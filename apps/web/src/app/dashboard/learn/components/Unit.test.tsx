import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';

import Unit from './Unit';
import { useUnitInteraction, UseUnitInteractionReturn } from '../hooks/useUnitInteraction';

vi.mock('../hooks/useUnitInteraction', () => ({
  useUnitInteraction: vi.fn(),
}));

vi.mock('./Module', () => ({
  default: ({ module }: { module: { title: string } }) => (
    <div>{module.title}</div>
  ),
}));

vi.mock('./LessonPath', () => ({
  default: () => <div data-testid="lesson-path" />,
}));

describe('Unit', () => {
  it('selects a lesson when clicked', () => {
    const toggleLessonSelection = vi.fn();

    const mockUnitInteraction: UseUnitInteractionReturn = {
        selectedLessonId: null,
        hoveredLessonId: null,
        isLessonSelected: vi.fn(),
        isLessonHovered: vi.fn(),
        selectLesson: vi.fn(),
        clearSelection: vi.fn(), 
        setHoveredLesson: vi.fn(),
        toggleLessonSelection,
    };

    vi.mocked(useUnitInteraction).mockReturnValue(mockUnitInteraction);

    // Use a valid Unit fixture matching your API schema.
    const unit = {
      id: 1,
      title: 'Introduction',
      modules: [
        { id: 101, title: 'Lesson One' },
      ],
    } as Parameters<typeof Unit>[0]['unit'];

    render(<Unit unit={unit} />);

    fireEvent.click(screen.getByText('Lesson One'));

    expect(toggleLessonSelection).toHaveBeenCalledWith(101);
  });
});