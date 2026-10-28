import { render, screen, fireEvent, within } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';

import Unit from './Unit';
import { useUnitInteraction, UseUnitInteractionReturn } from  './useUnitInteraction';

vi.mock('./useUnitInteraction', () => ({
  useUnitInteraction: vi.fn(),
}));

vi.mock('./Module', () => ({
  default: ({ module }: { module: { title: string } }) => (
    <div>{module.title}</div>
  ),
}));

vi.mock('./ModulePath', () => ({
  default: () => <div data-testid="Module-path" />,
}));

describe('Unit', () => {
  let toggleModuleSelection: ReturnType<typeof vi.fn>;
  let mockUnitInteraction: UseUnitInteractionReturn;
  let unit: Parameters<typeof Unit>[0]['unit'];

  beforeEach(() => {
    toggleModuleSelection = vi.fn();

    mockUnitInteraction = {
      selectedModuleId: null,
      hoveredModuleId: null,
      isModuleSelected: vi.fn(),
      isModuleHovered: vi.fn(),
      selectModule: vi.fn(),
      clearSelection: vi.fn(),
      setHoveredModule: vi.fn(),
      toggleModuleSelection,
    };

    vi.mocked(useUnitInteraction).mockReturnValue(mockUnitInteraction);

    unit = {
      id: 1,
      title: 'Introduction',
      modules: [{ id: 101, title: 'Module One' }],
    } as Parameters<typeof Unit>[0]['unit'];
  });

  it('selects a Module when clicked', () => {

    render(<Unit unit={unit} />);

    fireEvent.click(screen.getByText('Module One'));

    expect(toggleModuleSelection).toHaveBeenCalledWith(101);
  });

  it("deselects an open Module when clicked", ()=>{
    render(<Unit unit={unit} />);

    fireEvent.click(screen.getByText('Module One'));
    expect(toggleModuleSelection).toHaveBeenCalledWith(101);

    fireEvent.click(screen.getByText('Module One'));
    expect(toggleModuleSelection).toHaveBeenCalledWith(101);
  })

  it("renders Unit Text and all child modules", ()=>{
    const modules = [
      { id: 1, title: "Module 1", unit: 1, order: 1},
      { id: 2, title: "Module 2", unit: 1, order: 1 },
      { id: 3, title: "Module 3", unit: 1, order: 1 },
    ]

    unit = {
      id: 1,
      title: 'Introduction',
      modules: modules,
    } as Parameters<typeof Unit>[0]['unit'];

    render(<Unit unit={unit} />);

    const unit_component = screen.getByTestId("unit");

    expect(unit_component).toBeVisible();


    // Check that all Modules are visible
    modules.forEach((module) => {
      expect(within(unit_component).getByText(module.title)).toBeVisible();
    });
  })
});