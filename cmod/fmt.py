"""

format.py

Python helper function for helping with string formatting. This includes ASCII
color code injection. And well as additional formatting to be performed for
logging.

"""
import logging
import re


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
  default_format = '\033[1;32m[{cmdline:s}]\033[0m' + " {message:s}"

  format_lookup = {
      logging.ERROR: RED("[ERROR  ]") + default_format,
      logging.WARNING: YELLOW("[WARNING]") + default_format,
  }

  def __init__(self):
    pass

  def format(self, record):
    # Replace the original format with one customized by logging level
    fmt_str = self.format_lookup.get(record.levelno, self.default_format)
    fmt = logging.Formatter(fmt_str, style='{')
    record.msg = oneline_string(record.msg)
    return fmt.format(record)


class DeviceStreamFormatter(logging.Formatter):
  default_format = '\033[1;32m[{device:s}]\033[0m' + " {message:s}"

  format_lookup = {
      logging.ERROR: RED("[ERROR  ]") + default_format,
      logging.WARNING: YELLOW("[WARNING]") + default_format,
  }

  def __init__(self):
    pass

  def format(self, record):
    # Replace the original format with one customized by logging level
    fmt_str = self.format_lookup.get(record.levelno, self.default_format)
    fmt = logging.Formatter(fmt_str, style='{')
    if hasattr(record, 'device'):
      return fmt.format(record)
    else:
      m = re.match(r'\[\[(.*)\]\](.*)', record.msg)
      if m is not None:
        record.device = m.group(1)
        record.msg = m.group(2)
      return fmt.format(record)
