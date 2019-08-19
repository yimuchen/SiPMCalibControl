## Simple class for handling termination signals
## Solution take from
## https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully
import signal

class SigHandle:
  def __init__(self):
    self.terminate = False
    ## SIG_INT is Ctl+C
    signal.signal(signal.SIGINT, self.receive_term)
    signal.signal(signal.SIGTERM, self.receive_term)

  def receive_term(self, signum, frame):
    self.terminate = True

## Testing library
if __name__ == '__main__':
  import time

  sighandle = SigHandle()
  while not sighandle.terminate:
    time.sleep(1)
    print('doing something in a loop ...')

  print('End of the program. I was killed gracefully :)')