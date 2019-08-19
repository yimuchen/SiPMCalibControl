import paramiko
import getpass
import shutil
import cmod.logger as log
#import logger as log


class SSHFiler(paramiko.SSHClient):
  """
  Object for handling ssh file requests with host server
  """

  default_path = "/home/yichen/public/SiPMCalib/"

  def __init__(self):
    paramiko.SSHClient.__init__(self)
    self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    self.host = ""
    self.remotepath = SSHFiler.default_path

  def reconnect(self, remotehost):
    # Closing existing section
    if self.get_transport():
      self.sftp.close()
      self.close()

    ## Nothing is saved in memory!
    self.connect(remotehost,
                 username=input(
                     log.GREEN('Username at {0}: ').format(remotehost)),
                 password=getpass.getpass(
                     log.GREEN('Password at {0}: ').format(remotehost)),
                 compress=True)

    ## Magic settings for boosting speed
    self.get_transport().window_size = 2147483647
    self.get_transport().packetizer.REKEY_BYTES = pow(2, 40)
    self.get_transport().packetizer.REKEY_PACKETS = pow(2, 40)

    # Opening sftp stuff.
    self.sftp = self.open_sftp()
    self.host = remotehost

  def __del__(self):
    if self.get_transport():
      self.sftp.close()
      self.close()

  def remotefile(self, filename, wipefile):
    ## Always try to open in append mode
    if self.get_transport():
      if wipefile:
        return self.sftp.open(self.remotefilename(filename), 'w')
      else:
        return self.sftp.open(self.remotefilename(filename), 'a')
    else:
      if wipefile:
        return open(filename, 'w')
      else:
        return open(filename, 'a+')

  def remotefilename(self, filename):
    return str(self.remotepath + filename)

  def writeto(self, filename, data):
    f = self.remotefile(filename, False)
    f.write(data)
    f.close()

  def copyfile(self, localfile, remotefile):
    if self.get_transport():
      self.sftp.put(localfile, self.remotefilename(remotefile))
    else:
      shutil.copyfile(localfile, remotefile)

  def setremotepath(self, newpath):
    self.remotepath = newpath
    if not self.remotepath.endswith('/'):
      self.remotepath = self.remotepath + '/'


## For testing
if __name__ == "__main__":
  ssh = SSHFiler()
  ssh.reconnect('10.42.0.1')
  ssh.setremotepath('/data/ensc/Homework_Largefiles/StandTest')

  import random

  def randomstring():
    return ''.join(random.choice('0123456789abcedf') for x in range(250))

  for i in range(1000000):
    ssh.writeto('test.txt', randomstring() + '\n')
  #ssh.sftp.put("/tmp/test2.txt", "test2.txt")
