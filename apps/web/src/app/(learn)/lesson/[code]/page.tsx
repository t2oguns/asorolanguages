"use client"

import React from 'react'
import { useParams } from "next/navigation";
import { api } from '@/lib/api/api';
import { sampleLesson } from './sampleLesson';
import LessonPlayer from '@/components/features/lesson/LessonPlayer';

const Page =  () => {
    const { code } = useParams<{ code: string }>();
    const lesson  = api(`/api/v1/courses/lesson/{code}/`, {
        params: {path: {"code": code}}
    })

    if (!lesson) {
        return <div>Lesson not found.</div>;
    }

    function onComplete(){
        api(`/api/v1/courses/lesson/{code}/submit/`, {
            method:'post', 
            body:JSON.stringify({}),
            params: {path: {"code": code}}
        })
    }

    return (
    <div className='bg-white h-screen'>
        
        <LessonPlayer
        title="Basics: food and animals"
        exercises={sampleLesson}
        locale="es-ES"
        exitHref="/dashboard/learn/"
        onComplete={onComplete}
        />
    </div>
  )
}

export default Page