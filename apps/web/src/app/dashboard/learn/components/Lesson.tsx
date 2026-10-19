'use client'

import React from 'react'
import { useRouter } from 'next/navigation';
import type { components } from '@/lib/api-schema'

type LessonType = components["schemas"]["LessonDetail"]


const Lesson = ({lesson}: {lesson: LessonType}) => {
    const router = useRouter();
  /*const goToLesson = () => {
    router.push(`lesson/${lesson.code}/`);
  };*/

  return (
    <div className="lesson-info rounded-2xl w-7/16 h-48 px-0.5 text-center flex flex-col items-center">
        <h1 className="lesson-title text-md text-white font-bold">{lesson.title}</h1>
        <h4 className="lesson-description text-xs font-bold text-gray-300">{lesson.description}</h4>
        <button
          onClick={(e) => {
            e.stopPropagation();
            //goToLesson();
          }}
          className="bg-white rounded-lg py-1 text-sm font-bold mt-auto w-3/4 hover:text-gray-400"
        >
          Start Lesson
        </button>
      </div>
  )
}

export default Lesson