## Simple class for handling termination signals
## Solution take from
## https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully
import signal

class SigHandle:
  ORIGINAL_SIGINT = signal.getsignal(signal.SIGINT)
  ORIGINAL_SIGTERM = signal.getsignal(signal.SIGTERM)

  def __init__(self):
    self.terminate = False
    self.reset()
    ## SIG_INT is Ctl+C


  def receive_term(self, signum, frame):
    self.terminate = True

  def reset(self):
    self.terminate = False
    try:
      signal.signal(signal.SIGINT, self.receive_term)
      signal.signal(signal.SIGTERM, self.receive_term)
    except:
      pass

  def release(self):
    self.terminate = False
    try:
      ## Disabling signal handling by releasing the found function
      signal.signal(signal.SIGINT, SigHandle.ORIGINAL_SIGINT )
      signal.signal(signal.SIGTERM, SigHandle.ORIGINAL_SIGTERM )
    except:
      pass


## Testing library
if __name__ == '__main__':
  import time

  sighandle = SigHandle()
  index = 0
  while not sighandle.terminate:
    time.sleep(1)
    print('doing something in a loop ...')
    index = index +1
    if( index > 5 ):
      sighandle.release()

  print('End of the program. I was killed gracefully :)')