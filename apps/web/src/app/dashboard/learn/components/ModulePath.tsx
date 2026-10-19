'use client';

import React, { useMemo } from 'react';

interface Point {
  x: number;
  y: number;
}

interface ModulePathProps {
  positions: Point[];
  selectedIndex: number | null;
  height: number;
}

const createConnectorPath = (
  from: Point,
  to: Point,
) => {
  const midY = (from.y + to.y) / 2;

  return `
    M ${from.x} ${from.y}
    C ${from.x} ${midY},
      ${to.x} ${midY},
      ${to.x} ${to.y}
  `;
};

const ModulePath = ({
  positions,
  selectedIndex,
  height,
}: ModulePathProps) => {
  const connectors = useMemo(() => {
    return positions.slice(0, -1).map((from, index) => {
      const to = positions[index + 1];

      return {
        id: `${index}-${index + 1}`,
        path: createConnectorPath(from, to),
        isActive:
          index === selectedIndex ||
          index + 1 === selectedIndex,
        endpoint: to,
      };
    });
  }, [positions, selectedIndex]);

  return (
    <svg
      className="pointer-events-none absolute inset-0 z-0 h-full w-full overflow-visible"
      viewBox={`0 0 100 ${height}`}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      {connectors.map((connector) => (
        <React.Fragment key={connector.id}>
          <path
            d={connector.path}
            fill="none"
            stroke="currentColor"
            strokeWidth="0.16"
            strokeDasharray="0.65 0.8"
            strokeLinecap="round"
            className={[
              'transition-all duration-500',
              connector.isActive
                ? 'text-gray-400'
                : 'text-gray-300',
            ].join(' ')}
          />

          <circle
            cx={connector.endpoint.x}
            cy={connector.endpoint.y}
            r="0.3"
            className={
              connector.isActive
                ? 'fill-gray-400'
                : 'fill-gray-300'
            }
          />
        </React.Fragment>
      ))}
    </svg>
  );
};

export default ModulePath;