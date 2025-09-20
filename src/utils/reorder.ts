export const moveItem = <T>(list: T[], from: number, to: number) => {
  if (from === to) return;
  if (from < 0 || from >= list.length) return;

  const [item] = list.splice(from, 1);
  if (item === undefined) return;

  let targetIndex = to;
  if (targetIndex < 0) targetIndex = 0;
  if (targetIndex > list.length) targetIndex = list.length;

  list.splice(targetIndex, 0, item);
};
