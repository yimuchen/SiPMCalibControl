export const timestampToDate = (timestamp: string): Date => {
  var ret = new Date();
  ret.setFullYear(parseInt(timestamp.slice(0, 4)))
  ret.setMonth(parseInt(timestamp.slice(4, 6)))
  ret.setDate(parseInt(timestamp.slice(6, 8)))
  ret.setHours(parseInt(timestamp.slice(9, 11)))
  ret.setMinutes(parseInt(timestamp.slice(11, 13)))
  ret.setSeconds(parseInt(timestamp.slice(13, 15)))

  return ret

}
