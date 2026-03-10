/**
 * Extracts the best image URL from a list of images or returns a fallback.
 * @param images Array of Image objects
 * @param fallback Optional fallback URL
 */
export const getImageUrl = (images: any[], fallback: string = ''): string => {
  if (!images || images.length === 0) return fallback;
  // If images have width, sort by largest
  if (images[0].width) {
    return images.sort((a, b) => b.width - a.width)[0].url;
  }
  // Fallback to medium size (index 1) or first available
  return images[Math.min(1, images.length - 1)].url;
};
