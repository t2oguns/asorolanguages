'use client';

import React, { useMemo, useRef, useEffect } from 'react';
import type { components } from '@/lib/api/api-schema';

import Module from './Module';
import ModulePath from './ModulePath';

import { useUnitInteraction } from './useUnitInteraction';
import {generateWindingLayout, calculateSpreadPosition,type Point} from './module-layout';

type UnitType = components['schemas']['Unit'];

type Props = {
  unit: UnitType;
};

const ROW_HEIGHT = 15;

const DEFAULT_POSITION: Point = {
  x: 50,
  y: 0,
};

const Unit = ({ unit }: Props) => {
  
    const { selectedModuleId, toggleModuleSelection } = useUnitInteraction();

    const moduleRefs = useRef<Record<number, HTMLDivElement | null>>({});

    useEffect(() => {
        if (selectedModuleId == null) return;

        const frame = requestAnimationFrame(() => {
            moduleRefs.current[selectedModuleId]?.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'center',
            });
        });

        return () => cancelAnimationFrame(frame);
    }, [selectedModuleId]);

    /**
     * Generate base positions.
     */
    const modulePositions = useMemo(() => {
    
        const generated =
            generateWindingLayout(unit.modules.length, {
            leftX: 15,
            rightX: 57,
            rowSpacing: 1,
            startY: 0.5,
            organicOffset: 3,
            });

        const positions = new Map<number, Point>();

        unit.modules.forEach((module, index) => {
            positions.set(
            module.id,
            generated[index] ?? DEFAULT_POSITION,
            );
        });

        return positions;
    
    }, [unit.modules]);

    /**
     * Selected module's base position.
     */
    const selectedPosition =
    selectedModuleId !== null
        ? modulePositions.get(selectedModuleId) ?? null
        : null;

    /**
     * Calculate final visual positions.
     */
    const positions = useMemo(() => {
        const result = new Map<number, Point>();

        unit.modules.forEach((module) => {
            const originalPosition =
            modulePositions.get(module.id) ??
            DEFAULT_POSITION;

            const isModuleSelected =
            module.id === selectedModuleId;

            result.set(
                module.id,
                calculateSpreadPosition(
                    originalPosition,
                    selectedPosition,
                    isModuleSelected,
                ),
            );
        });

        return result;
    }, [unit.modules, modulePositions, selectedModuleId, selectedPosition]);

    /*
     * Convert positions to the array format
     * expected by modulePath.
    */
    const pathPositions = useMemo(() => {
        return unit.modules.map(
            (module) =>
            positions.get(module.id) ??
            DEFAULT_POSITION,
        );
    }, [unit.modules, positions]);

    /*
     * Find selected module index for path styling.
    */
    const selectedIndex = useMemo(() => {
        if (selectedModuleId === null) {
            return null;
        }

        const index = unit.modules.findIndex(
            (module) => module.id === selectedModuleId,
        );

        return index === -1 ? null : index;
    }, [unit.modules, selectedModuleId]);

    const canvasHeight = Math.max(ROW_HEIGHT, unit.modules.length * ROW_HEIGHT);

    const canvasRows = Math.max(unit.modules.length, 1);

    return (
        <section className="flex min-h-screen w-full snap-start flex-col pt-6" data-testid="unit">
            {/* Unit heading */}
            <header className="w-fit text-right">
                <p className="text-xl font-semibold text-gray-500">
                    Unit {unit.id}
                </p>

                <h2 className="text-2xl font-bold text-black">
                    {unit.title}
                </h2>
            </header>

            {/* module path */}
            <div
                className="relative mt-6 w-full"
                style={{
                    height: `${canvasHeight}rem`,
                }}
            >
            <ModulePath
                positions={pathPositions}
                selectedIndex={selectedIndex}
                height={canvasRows}
            />

            {unit.modules.map((module) => {
                const isModuleSelected = selectedModuleId === module.id;

                const position = positions.get(module.id) ?? DEFAULT_POSITION;

                return (
                <div
                    key={module.id}
                    className={[
                        'absolute cursor-pointer  opacity-90',
                        'transition-all duration-500 ease-out',
                        'will-change-[left,top,width,height]',
                        isModuleSelected
                            ? 'z-20 h-[17rem] w-[min(27rem,90vw)] shadow-xl'
                            : 'z-10 h-[12rem] w-[12rem]',
                        ].join(' ')}
                    style={{
                        left: `${position.x}%`,
                        top: `${(position.y / canvasRows) * 100}%`,
                        transform: 'translate(-50%, -50%)',
                    }}
                    ref={(element) => {
                        moduleRefs.current[module.id] = element;
                    }}
                    onClick={() => toggleModuleSelection(module.id)}
                >
                    <Module isModuleSelected={isModuleSelected} module={module}/>
                </div>
                );
            })}
            </div>
        </section>
    );
};

export default Unit;