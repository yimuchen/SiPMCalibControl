import cmod.visual as vis
import time
import cv2

myvis = vis.Visual()
myvis.init_dev("/dev/video0")
time.sleep(1)
for i in range(100000):
  latest = myvis.get_latest()
  image = myvis.get_image()
  cv2.imshow('image',image )
  cv2.waitKey(1)
  time.sleep(0.01)

cv2.destroyAllWindows()