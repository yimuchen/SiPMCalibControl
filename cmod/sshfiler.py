import paramiko
import getpass
import shutil
import cmod.logger as logger

class SSHFiler(paramiko.SSHClient):
  """
  Object for handling ssh file requests with host server
  """

  default_path = "/home/yichen/public/SiPMCalib/"

  def __init__(self):
    paramiko.SSHClient.__init__(self)
    self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # self.reconnect()

  def reconnect(self):
    # Closing existing section
    if self.get_transport():
      self.sftp.close()
      self.close()
    ## Connecting immediately
    ## Nothing is saved in memory!

    host = input( logger.GREEN("Remote machine [ex. hepcms.umd.edu]: ") )

    if host:
      self.connect(
        host,
        username=input(logger.GREEN("Username at {0}: ").format(SSHFiler.host)),
        password=getpass.getpass(
            logger.GREEN("Password at {0}: ").format(SSHFiler.host)))
    # Opening sftp stuff.
      self.sftp = self.open_sftp()
    else:
      logger.printmsg( "Skipping login... storing file to local" )

  def __del__(self):
    if self.get_transport():
      self.sftp.close()
      self.close()

  def remotefile(self, filename):
    ## Always try to open in append mode
    if self.get_transport():
      return self.sftp.open(self.remotefilename(filename), 'a+')
    else:
      return open(filename, 'a+')

  def remotefilename(self, filename):
    return str(SSHFiler.default_path + filename)

  def writeto(self, filename, data):
    f = self.remotefile(filename)
    f.write(data)
    f.close()

  def copyfile(self, localfile, remotefile ):
    if self.get_transport():
      self.sftp.put( localfile, self.remotefilename(remotefile) )
    else:
      shutil.copyfile( localfile, remotefile )




## For testing
if __name__ == "__main__":
  ssh = SSHFiler()
  ssh.writeto('test.txt', "Class test!")
  ssh.sftp.put("/tmp/test2.txt", "test2.txt")
