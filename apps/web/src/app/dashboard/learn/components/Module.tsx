import React from 'react'
import type { components } from '@/lib/api-schema'
import Lesson from './Lesson';

type ModuleType = components["schemas"]["Module"]


type Props = {
    isModuleSelected: boolean;
    module: ModuleType;
};

const Module = ({isModuleSelected, module}: Props) => {

  // Should be able to switch between lesson and should default to the un completed of the lessons or the last one
  const lesson = module.lessons[0] ?? {title: "", description: "", code: null, order: null };

  return isModuleSelected ? (
    <div className="bg-linear-to-br from-ewe-300/90 to-ewe-500/90 backdrop-blur-md h-full w-full rounded-3xl flex flex-row items-center justify-evenly">
      <div className="bg-white h-30 w-30 rounded-3xl"></div>
      <Lesson lesson={lesson}/>
    </div>
  ) : (
    <div className="w-full h-full bg-linear-to-br from-ewe-300 to-ewe-500 opacity-90 flex rounded-3xl items-center text-white justify-center">
      <div className="bg-ewe-500/70 h-3/4 w-3/4 rounded-xl"></div>
    </div>
  );
}

export default Module