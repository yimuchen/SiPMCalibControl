import paramiko
import getpass
import cmod.logger as logger

class SSHFiler(paramiko.SSHClient):
  """
  Object for handling ssh file requests with host server
  """

  host = "hepcms.umd.edu"
  default_path = "/home/yichen/public/SiPMCalib/"

  def __init__(self):
    paramiko.SSHClient.__init__(self)
    self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    self.reconnect()

  def reconnect(self):
    # Closing existing section
    if self.get_transport():
      self.close()
    ## Connecting immediately
    ## Nothing is saved in memory!
    self.connect(
        SSHFiler.host,
        username=input(logger.GREEN("Username at {0}: ").format(SSHFiler.host)),
        password=getpass.getpass(
            logger.GREEN("Password at {0}: ").format(SSHFiler.host)))
    # Opening sftp stuff.
    self.sftp = self.open_sftp()

  def __del__(self):
    if self.get_transport():
      self.close()

  def remotefile(self, filename):
    ## Always try to open in append mode
    if self.get_transport():
      return self.sftp.open(SSHFiler.default_path + filename, 'a+')
    else:
      return open(filename, 'a+')

  def writeto(self, filename, data):
    f = self.remotefile(filename)
    f.write(data)
    f.close()


## For testing
if __name__ == "__main__":
  ssh = SSHFiler()
  ssh.writeto('test.txt', "Class test!")
