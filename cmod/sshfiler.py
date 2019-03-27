import paramiko
import getpass
import shutil
import cmod.logger as log


class SSHFiler(paramiko.SSHClient):
  """
  Object for handling ssh file requests with host server
  """

  default_path = "/home/yichen/public/SiPMCalib/"

  def __init__(self):
    paramiko.SSHClient.__init__(self)
    self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    self.host = ""
    self.remotepath =  "/home/yichen/public/SiPMCalib/"

  def reconnect(self, remotehost):
    # Closing existing section
    if self.get_transport():
      self.sftp.close()
      self.close()

    ## Nothing is saved in memory!
    self.connect(
        remotehost,
        username=input(log.GREEN("Username at {0}: ").format(SSHFiler.host)),
        password=getpass.getpass(
            log.GREEN("Password at {0}: ").format(SSHFiler.host)))
    # Opening sftp stuff.
    self.sftp = self.open_sftp()
    self.host = ""

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
        return open(filename, 'a')

  def remotefilename(self, filename):
    return str(self.remotepath + filename)

  def writeto(self, filename, data):
    f = self.remotefile(filename)
    f.write(data)
    f.close()

  def copyfile(self, localfile, remotefile):
    if self.get_transport():
      self.sftp.put(localfile, self.remotefilename(remotefile))
    else:
      shutil.copyfile(localfile, remotefile)


## For testing
if __name__ == "__main__":
  ssh = SSHFiler()
  ssh.writeto('test.txt', "Class test!")
  ssh.sftp.put("/tmp/test2.txt", "test2.txt")
