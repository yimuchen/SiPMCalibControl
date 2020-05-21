from . import session

import copy
import datetime


def CalibDirectory():
  timestamp_string = session.calib_session_time.strftime('%Y%m%d-%H%M')
  return 'results/{boardtype}_{boardid}_{timestamp}'.format(
      boardtype=session.cmd.board.boardtype,
      boardid=session.cmd.board.boardid,
      timestamp=timestamp_string)


def CalibFilename(prefix, detid=None):
  if detid:
    return '{dir}/{prefix}_det{det}.txt'.format(dir=CalibDirectory(),
                                                prefix=prefix,
                                                det=detid)
  else:
    return '{dir}/{prefix}.json'.format(dir=CalibDirectory(),
                                        prefix=prefix,
                                        det=detid)


"""
Generation of stanard calibration commands
"""


def ReduceCmdSpaces(ans):
  return ' '.join(ans.split())


def CmdZScan(detid, dense, rev):
  z_list = []

  ## Choosing the density
  if dense:
    z_list = copy.copy(session.zscan_zlist_dense)
  else:
    z_list = copy.copy(session.zscan_zlist_sparse)

  ## Whether or not to reverse the ordering
  if rev: z_list = reversed(z_list)

  ans = """
  zscan --detid={detid}   --channel={detid} --zlist {zlist}
        --sample=100      --power {powerlist}
        --savefile={file} --wipefile
  """.format(detid=detid,
             zlist=' '.join([str(z) for z in z_list]),
             powerlist=' '.join([str(p) for p in session.zscan_power_list]),
             file=CalibFilename('zscan', detid))

  return ReduceCmdSpaces(ans)


def CmdLowLightCollect(detid):
  ans = """
  lowlightcollect --detid {detid}  --sample 10000 --channel={detid}
                  --power  0.5     -z {zmax}
                  --savefile={file}    --wipefile
  """.format(detid=detid, zmax=300, file=CalibFilename('lowlight', detid))
  return ReduceCmdSpaces(ans)


def CmdLumiAlign(detid):
  ans = """
  halign --detid={detid} --channel={detid}
         --sample=100 -z 10  --overwrite
         --range=6 --distance=3
         --power=0.5
         -f={filename}
         --wipefile
  """.format(detid=detid, filename=CalibFilename('halign', detid))
  return ReduceCmdSpaces(ans)
