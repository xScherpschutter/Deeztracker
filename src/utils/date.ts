export function getRelativeTime(dateStr: string, t: any): string {
  // Convertir el formato de SQLite (YYYY-MM-DD HH:MM:SS) a ISO para que JS lo entienda correctamente
  const date = new Date(dateStr.replace(' ', 'T') + 'Z'); 
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return t('library.date_relative.now');
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return t('library.date_relative.minutes', { n: diffInMinutes });
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return t('library.date_relative.hours', { n: diffInHours });
  }

  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) {
    return t('library.date_relative.days', { n: diffInDays });
  }

  const diffInWeeks = Math.floor(diffInDays / 7);
  if (diffInWeeks < 4) {
    return t('library.date_relative.weeks', { n: diffInWeeks });
  }

  const diffInMonths = Math.floor(diffInDays / 30);
  if (diffInMonths < 12) {
    return t('library.date_relative.months', { n: diffInMonths });
  }

  const diffInYears = Math.floor(diffInDays / 365);
  return t('library.date_relative.years', { n: diffInYears });
}
