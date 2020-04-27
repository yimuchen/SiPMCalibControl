chipid_list = range(64)
z_list = list(range(10, 20, 2))
z_list.extend(range(20, 100, 10))
z_list.extend(range(100, 350, 50))

## Visual calibration stuff
for row in range(8):
  for column in range(8):
    chipid = -1
    if row % 2 == 0:
      chipid = 8 * row + column
    else:
      chipid = 8 * (row + 1) - column - 1

    print('visualcenterchip --chipid {chipid} -z {z} --overwrite'.format(
        chipid=chipid, z=min(z_list)))

for row in range(8):
  for column in range(8):
    chipid = -1
    if row % 2 == 0:
      chipid = 8 * row + column
    else:
      chipid = 8 * (row + 1) - column - 1

    if z_list[0] > z_list[1]:
      print(
          'lowlightcollect --chipid {chipid} --sample 100000 -z {z} --wipefile'.
          format(chipid=chipid, z=z_list[0]))
    zscan_line = 'zscan --chipid {chipid} --zlist {l} --sample 100 --wipefile'.format(
        chipid=chipid, l=' '.join([str(z) for z in z_list]))
    print(zscan_line)
    if z_list[0] < z_list[1]:
      print(
          'lowlightcollect --chipid {chipid} --sample 100000 -z {z} --wipefile'.
          format(chipid=chipid, z=z_list[-1]))

    z_list.reverse()
