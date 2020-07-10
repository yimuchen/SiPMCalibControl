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
  zscan --detid={detid}
        --channel={channel} --mode={mode}
        --zlist {zlist}
        --sample={samples}      --power {powerlist}
        --savefile={file} --wipefile
  """.format(detid=detid,
             samples=session.zscan_samples,
             mode=session.cmd.board.get_det(detid).mode,
             channel=session.cmd.board.get_det(detid).channel,
             zlist=' '.join([str(z) for z in z_list]),
             powerlist=' '.join([str(p) for p in session.zscan_power_list]),
             file=CalibFilename('zscan', detid))

  return ReduceCmdSpaces(ans)


def CmdLowLightCollect(detid):
  ans = """
    lowlightcollect --detid {detid}  --sample {samples}
                    --mode={mode}
                    --channel={channel}
                    --power  0.75    -z {zval}
                    --savefile={file}    --wipefile
    """.format(detid=detid,
               samples=session.lowlight_samples,
               mode=session.cmd.board.get_det(detid).mode,
               channel=session.cmd.board.get_det(detid).channel,
               zval=session.lowlight_zval,
               file=CalibFilename('lowlight', detid))

  return ReduceCmdSpaces(ans)


def CmdLumiAlign(detid):
  ans = """
    halign --detid={detid}
           --channel={channel} --mode={mode}
           --sample={samples} -z {zval}  --overwrite
           --range={range} --distance={distance}
           --power={power}
           -f={filename}
           --wipefile
    """.format(detid=detid,
               mode=session.cmd.board.get_det(detid).mode,
               channel=session.cmd.board.get_det(detid).channel,
               samples=session.lumialign_samples,
               zval=session.lumialign_zval,
               range=session.lumialign_range,
               distance=session.lumialign_distance,
               power=session.lumialign_pwm,
               filename=CalibFilename('halign', detid))
  return ReduceCmdSpaces(ans)


def CmdVisualAlign(detid):
  ans = """
  visualcenterdet --detid {detid}
                  -z 20
                  --overwrite
  """.format(detid=detid)
  return ReduceCmdSpaces(ans)