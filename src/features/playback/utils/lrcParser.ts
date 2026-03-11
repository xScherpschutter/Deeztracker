export interface LrcLine {
  timeMs: number;
  text: string;
}

export class LrcParser {
  // Matches [mm:ss.xx] or [mm:ss]
  private static readonly TIMESTAMP_REGEX = /\[(\d+):(\d+(?:\.\d+)?)\]/g;

  static parse(lrcContent: string): LrcLine[] {
    if (!lrcContent || lrcContent.trim() === "") return [];

    // Sanitize: Handle literal \n text
    const cleanContent = lrcContent.replace(/\\n/g, "\n");

    const lines: LrcLine[] = [];
    let foundSyncedLine = false;

    const contentLines = cleanContent.split("\n");

    for (const line of contentLines) {
      const trimmedLine = line.trim();
      if (trimmedLine === "") continue;

      // Find all timestamps in the line
      const matches = Array.from(trimmedLine.matchAll(this.TIMESTAMP_REGEX));

      if (matches.length > 0) {
        foundSyncedLine = true;
        // The text is everything after the last timestamp
        const lastMatch = matches[matches.length - 1];
        const lastMatchEndIndex = (lastMatch.index || 0) + lastMatch[0].length;
        const text = trimmedLine.substring(lastMatchEndIndex).trim();

        for (const match of matches) {
          const min = parseInt(match[1], 10) || 0;
          const sec = parseFloat(match[2]) || 0;

          const timeMs = Math.round((min * 60 + sec) * 1000);
          lines.push({ timeMs, text });
        }
      }
    }

    // Fallback: If no timestamps were found, treat as plain lyrics
    if (!foundSyncedLine && lines.length === 0) {
      for (const line of contentLines) {
        if (line.trim() !== "") {
          // Use Number.MAX_SAFE_INTEGER so they are never "active" for auto-scroll
          lines.push({ timeMs: Number.MAX_SAFE_INTEGER, text: line.trim() });
        }
      }
    }

    return lines.sort((a, b) => a.timeMs - b.timeMs);
  }

  static getActiveLineIndex(lyrics: LrcLine[], positionMs: number): number {
    if (lyrics.length === 0) return -1;

    // If plain lyrics (MAX_SAFE_INTEGER), never highlight
    if (lyrics[0].timeMs === Number.MAX_SAFE_INTEGER) return -1;

    let low = 0;
    let high = lyrics.size - 1; // Wait, size is for Java, use length
    high = lyrics.length - 1;
    let result = -1;

    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      const line = lyrics[mid];

      if (line.timeMs <= positionMs) {
        result = mid;
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }
    return result;
  }
}
