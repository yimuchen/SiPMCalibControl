"""

format.py

Python helper function for helping with string formatting. This includes ASCII
color code injection. And well as additional formatting to be performed for
logging.

"""
import logging
import re
import copy
import traceback


def make_color_text(message: str, colorcode: int) -> str:
  """Adding ASCII color headers around message string"""
  return f"\033[1;{colorcode:d}m{message}\033[0m"


def RED(message: str) -> str:
  return make_color_text(message, 31)


def GREEN(message: str) -> str:
  return make_color_text(message, 32)


def YELLOW(message: str) -> str:
  return make_color_text(message, 33)


def CYAN(message: str) -> str:
  return make_color_text(message, 36)


def oneline_string(text):
  """
  Simplifying multiline text in python to a single line text in python, which
  also removes the additional whitespaces at the beginning of lines
  """
  return ' '.join(text.split())


# Custom output formatter
class CmdStreamFormatter(logging.Formatter):
  default_format = '\033[1;32m[{name:s}]\033[0m' + " {message:s}"

  def __init__(self):
    super().__init__(self.default_format, style='{')
    pass

  def format(self, record):
    format_lookup = {
        logging.ERROR: RED("[ERROR  ]") + self.default_format,
        logging.WARNING: YELLOW("[WARNING]") + self.default_format,
        logging.TRACE: YELLOW("[TRACE  ]") + self.default_format
    }
    # Replace the original format with one customized by logging level
    fmt_str = format_lookup.get(record.levelno, self.default_format)

    # Additional parsing of the record message for trace back.
    if record.levelno == logging.TRACE:
      record.msg = self.format_traceback(record.msg)

    # Common formatting
    record.name = '.'.join(record.name.split('.')[1:])  # removing the leading
    record.msg = oneline_string(record.msg)  # Reducing message new lines
    header_len = len(record.name) + 12  if record.levelno in format_lookup else \
                 len(record.name) + 3   # Length of header
    record.msg = record.msg.replace('<br>', '\n' + ' ' * header_len)

    formatter = logging.Formatter(fmt_str, style='{')
    return formatter.format(record)

  @staticmethod
  def format_traceback(traceback_str):
    exc_msg = traceback.format_exc()
    exc_msg = exc_msg.splitlines()
    exc_msg = exc_msg[1:-1]  ## Remove traceback and error line.
    lines = []
    for idx in range(0, len(exc_msg), 2):
      file = re.findall(r'\"[A-Za-z0-9\/\.]+\"', exc_msg[idx])
      if len(file):  # For non-conventional error messages
        file = file[0].strip().replace('"', '')
      else:
        continue

      lno = re.findall(r'line\s[0-9]+', exc_msg[idx])
      if len(lno):  # For non-conventional error messages
        lno = [int(s) for s in lno[0].split() if s.isdigit()][0]
      else:
        continue

      content = exc_msg[idx + 1].strip()
      lines.append(CYAN(f'{lno:4d}L|') + YELLOW(f'{file}| ') + content)
    return '<br>'.join(lines)
