export function cn(...classes: (string | boolean | undefined | null | {[key: string]: boolean})[]) {
  const result: string[] = [];
  classes.forEach((c) => {
    if (!c) return;
    if (typeof c === 'string') {
      result.push(c);
    } else if (typeof c === 'object') {
      Object.entries(c).forEach(([key, val]) => {
        if (val) result.push(key);
      });
    }
  });
  return result.join(' ');
}
