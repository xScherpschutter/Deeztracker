/**
 * Common drag and drop utilities
 */

/**
 * Handles the start of a drag event for a track or any JSON-serializable object.
 * @param e The DragEvent
 * @param data The data to be transferred (usually a Track object)
 * @param format The MIME type format (defaults to 'application/json')
 */
export const handleDragStart = (e: DragEvent, data: any, format = 'application/json') => {
  if (e.dataTransfer) {
    const jsonData = typeof data === 'string' ? data : JSON.stringify(data);
    e.dataTransfer.setData(format, jsonData);
    e.dataTransfer.effectAllowed = 'move';
    
    // Optional: Set a drag image or custom styling if needed in the future
  }
};
