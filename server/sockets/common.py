## Commonly used functions


def gen_cmdline_options(data, options_list):
  cmdline = [
      '--{0} {1}'.format(opt, data[opt]) for opt in options_list if opt in data
  ]
  cmdline = ' '.join(cmdline)
  return cmdline