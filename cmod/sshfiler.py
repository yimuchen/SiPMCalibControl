import paramiko
import getpass
import shutil
import os
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
    self.remotepath = SSHFiler.default_path

    ## Objects for holding the read/write file objects
    self.writefile = None
    self.readfile = None

  def reconnect(self, remotehost):
    # Closing existing section
    if self.get_transport():
      self.sftp.close()
      self.close()

    ## TODO: Use local user SSH config for kerberose settings as well
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
    """
    Here we open the file once for writing and once for writing. In this case,
    any update to the file can be monitored by the readfile.read() method.
    Allowing for easier interactions between systems.
    """
    if self.writefile and not self.writefile.closed:
      self.writefile.close()
    if self.readfile and not self.readfile.closed:
      self.readfile.close()

    ## Always try to open in append mode
    if self.get_transport():
      w_mode = 'w' if wipefile else 'a'
      self.writefile = self.sftp.open(self.remotefilename(filename), w_mode)
      self.readfile = self.sftp.open(self.remotefilename(filename), 'r')
    else:
      # For local files, try to create the parent directory if it doesn't
      # already exist.
      if os.path.dirname(filename) and not os.path.isdir(
          os.path.dirname(filename)):
        os.mkdir(os.path.dirname(filename))
      w_mode = 'w' if wipefile else 'a+'
      self.writefile = open(filename, w_mode)
      self.readfile = open(filename, 'r')
    return self.writefile

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
  ssh.reconnect('192.168.1.160')
  ssh.setremotepath('/data/ensc/Homework/SiPMCalib')

  import random

  def randomstring():
    return ''.join(random.choice('0123456789abcedf') for x in range(65536))

  remotefile = ssh.remotefile('test.txt', True)
  for i in range(10000):
    remotefile.write(randomstring() + '\n')
    # remotefile.flush()
  #ssh.sftp.put("/tmp/test2.txt", "test2.txt")
