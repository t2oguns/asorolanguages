import type { Media as MediaAsset } from '../types';

export default function Media({ asset }: { asset?: MediaAsset | null }) {
  if (!asset?.url) return null;
  if (asset.media_type === 'audio') return <audio controls preload="none" src={asset.url} aria-label={asset.alt_text || 'Pronunciation'} />;
  if (asset.media_type === 'video') return <video controls preload="metadata" src={asset.url} aria-label={asset.alt_text || 'Lesson video'} className="max-h-80 w-full rounded-2xl" />;
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={asset.url} alt={asset.alt_text || ''} className="max-h-80 rounded-2xl object-contain" />;
}
