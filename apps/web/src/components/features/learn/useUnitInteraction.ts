'use client';

import { useCallback, useState } from 'react';

export type ModuleId = number;

export interface UseUnitInteractionReturn {
  selectedModuleId: ModuleId | null;
  hoveredModuleId: ModuleId | null;

  isModuleSelected: (ModuleId: ModuleId) => boolean;
  isModuleHovered: (ModuleId: ModuleId) => boolean;

  selectModule: (ModuleId: ModuleId) => void;
  clearSelection: () => void;
  toggleModuleSelection: (ModuleId: ModuleId) => void;

  setHoveredModule: (ModuleId: ModuleId | null) => void;
}

export const useUnitInteraction = (): UseUnitInteractionReturn => {
  const [selectedModuleId, setSelectedModuleId] =
    useState<ModuleId | null>(null);

  const [hoveredModuleId, setHoveredModuleId] =
    useState<ModuleId | null>(null);

  /**
   * Select a Module explicitly.
   */
  const selectModule = useCallback((ModuleId: ModuleId) => {
    setSelectedModuleId(ModuleId);
  }, []);

  /**
   * Clear the current selection.
   */
  const clearSelection = useCallback(() => {
    setSelectedModuleId(null);
  }, []);

  /**
   * Toggle selection.
   *
   * Clicking the selected Module again
   * will deselect it.
   */
  const toggleModuleSelection = useCallback(
    (ModuleId: ModuleId) => {
      setSelectedModuleId((currentId) =>
        currentId === ModuleId
          ? null
          : ModuleId,
      );
    },
    [],
  );

  /**
   * Check whether a Module is selected.
   */
  const isModuleSelected = useCallback(
    (ModuleId: ModuleId) =>
      selectedModuleId === ModuleId,
    [selectedModuleId],
  );

  /**
   * Check whether a Module is hovered.
   */
  const isModuleHovered = useCallback(
    (ModuleId: ModuleId) =>
      hoveredModuleId === ModuleId,
    [hoveredModuleId],
  );

  return {
    selectedModuleId,
    hoveredModuleId,

    isModuleSelected,
    isModuleHovered,

    selectModule,
    clearSelection,
    toggleModuleSelection,

    setHoveredModule: setHoveredModuleId,
  };
};