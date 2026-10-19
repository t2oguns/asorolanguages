export interface Point {
  x: number;
  y: number;
}

export interface LayoutOptions {
  leftX?: number;
  rightX?: number;
  rowSpacing?: number;
  startY?: number;
  organicOffset?: number;
}

const clamp = (
  value: number,
  min: number,
  max: number,
) => Math.min(Math.max(value, min), max);

/**
 * Generate a winding layout.
 *
 * This function knows nothing about:
 * - React
 * - Lesson data
 * - Selection
 * - Hover
 * - API models
 *
 * It only generates coordinates.
 */
export const generateWindingLayout = (
  count: number,
  options: LayoutOptions = {},
): Point[] => {
  const {
    leftX = 20,
    rightX = 55,
    rowSpacing = 1,
    startY = 0.5,
    organicOffset = 3,
  } = options;

  return Array.from({ length: count }, (_, index) => {
    const isLeft = index % 2 === 0;

    const baseX = isLeft ? leftX : rightX;

    const xVariation =
      Math.sin(index * 1.4) * organicOffset;

    const yVariation =
      Math.cos(index * 1.2) * 0.08;

    return {
      x: clamp(baseX + xVariation, 5, 95),
      y: startY + index * rowSpacing + yVariation,
    };
  });
};

export const calculateSpreadPosition = (
  position: Point,
  selectedPosition: Point | null,
  isSelected: boolean,
): Point => {
  if (!selectedPosition || isSelected) {
    return position;
  }

  const dx = position.x - selectedPosition.x;
  const dy = position.y - selectedPosition.y;

  const distance = Math.sqrt(
    dx * dx + dy * dy,
  );

  const influenceRadius = 2.5;
  const maxSpread = 0.22;

  const normalizedDistance = clamp(
    distance / influenceRadius,
    0,
    1,
  );

  const influence =
    1 - normalizedDistance * normalizedDistance;

  const spreadFactor =
    1 + influence * maxSpread;

  return {
    x: clamp(
      selectedPosition.x + dx * spreadFactor,
      5,
      95,
    ),
    y: selectedPosition.y + dy * spreadFactor,
  };
};