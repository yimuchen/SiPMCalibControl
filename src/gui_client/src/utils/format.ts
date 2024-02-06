// Converting default timestamp in python to Javascript Date
export const timestampToDate = (timestamp: string): Date => {
  var ret = new Date();
  ret.setFullYear(parseInt(timestamp.slice(0, 4)));
  ret.setMonth(parseInt(timestamp.slice(4, 6)));
  ret.setDate(parseInt(timestamp.slice(6, 8)));
  ret.setHours(parseInt(timestamp.slice(9, 11)));
  ret.setMinutes(parseInt(timestamp.slice(11, 13)));
  ret.setSeconds(parseInt(timestamp.slice(13, 15)));
  return ret;
}


// Converting date to short display string
export const dateString = (d: Date): string => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const pad_zero = (x: number): string => {
    return String(x).padStart(2, '0');
  };
  const date_str = `${d.getFullYear()}.${months[d.getMonth()]}.${pad_zero(d.getDate())}`;
  const time_str = `${pad_zero(d.getHours())}:${pad_zero(d.getMinutes())}:${pad_zero(d.getSeconds())}`;
  const tz_str = (d.getTimezoneOffset() > 0) ? `${d.getTimezoneOffset() / 60}` : `+${-d.getTimezoneOffset() / 60}`;
  return `${date_str}@${time_str}(UTC${tz_str}hr)`;
}

export const timestampString = (timestamp: string): string => {
  return dateString(timestampToDate(timestamp));
}

// Converting session status into a a string 
export const statusIntToString = (status: number): string => {
  switch (status) {
    case 0:
      return "Action complete (IDLE)";
    case 1:
      return "Running";
    case 2:
      return "Last action errored!";
    case 3:
      return "Waiting user action"
    case 4:
      return "User interuptered!"
    default:
      return "UNKNOWN!!!";
  };
}

export const statusIntToShortString = (status: number): string => {
  switch (status) {
    case 0:
      return "Complete";
    case 1:
      return "Running";
    case 2:
      return "Error";
    case 3:
      return "Wait User"
    case 4:
      return "Interupt"
    default:
      return "UNKNOWN";
  };
}

