## Commonly used functions

from . import session

from time import sleep


def MessageUserAction(socketio, msg):
  socketio.emit('useraction', msg, namespace='/sessionsocket', broadcast=True)


def WaitUserAction(socketio, msg):
  print('Sending user action stuff', msg)
  MessageUserAction(socketio, msg)
  session.state = session.STATE_WAIT_USER
  session.waiting_msg = msg
  while (session.state == session.STATE_WAIT_USER):
    sleep(0.1)  ## Updating every 0.1 seconds


def CompleteUserAction(socketio):
  print('User action completed')
  session.state = session.STATE_RUN_PROCESS
  session.waiting_msg = ""


def ReturnClearExisting(socketio):
  socketio.emit('clear-display', '', broadcast=True, namespace='/sessionsocket')


def DisplayMessage(socketio, msg):
  socketio.emit('display-message',
                msg,
                boardcast=True,
                namespace='/sessionsocket')

def RunCmdInput(msg):
  execute_cmd = msg['input']
  session.cmd.onecmd(execute_cmd)
