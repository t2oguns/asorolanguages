import LessonPlayer from '@/components/features/lesson/LessonPlayer';

export default async function Page({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  return <LessonPlayer key={code} code={code} />;
}
