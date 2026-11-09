import { useState } from 'react';
import { resolveMediaSources } from '../services/media';

function DefaultFallback() {
  return <span aria-hidden="true">Imagen no disponible</span>;
}

export default function MediaImage({ sources, fallback, alt, onError, ...imageProps }) {
  // Sources are tried in order. Callers pass the stored file first and the
  // historical external URL second; a visual fallback is the final state.
  const candidates = resolveMediaSources(sources);
  const sourceKey = candidates.join('\n');
  const [failure, setFailure] = useState({ sourceKey, index: 0 });
  const currentIndex = failure.sourceKey === sourceKey ? failure.index : 0;
  const currentSource = candidates[currentIndex];

  if (!currentSource) {
    return (
      <span
        className="media-image-fallback"
        role="img"
        aria-label={alt || 'Imagen no disponible'}
        style={imageProps.style}
      >
        {fallback || <DefaultFallback />}
      </span>
    );
  }

  const handleError = event => {
    onError?.(event);
    setFailure({ sourceKey, index: currentIndex + 1 });
  };

  return <img {...imageProps} src={currentSource} alt={alt || ''} onError={handleError} />;
}
