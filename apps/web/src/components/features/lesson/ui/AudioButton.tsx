import { speakText } from '../lib/audio';
import { focusRing } from './ui';

export default function AudioButton({ text, locale }: { text?: string; locale: string }) {
  if (!text) return null;
  return (
    <button
      type="button"
      onClick={() => speakText(text, locale)}
      aria-label="Play audio"
      className={`size-11 flex-none rounded-full bg-blue-50 text-lg hover:bg-blue-100 ${focusRing}`}
    >
      🔊
    </button>
  );
}