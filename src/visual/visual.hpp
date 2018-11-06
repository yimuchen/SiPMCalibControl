/**
 * @file visual.hpp
 * @date 2018-10-26
 */
#ifndef VISUAL_HPP
#define VISUAL_HPP

#include <opencv2/videoio.hpp>
#include <opencv2/highgui/highgui.hpp>

class Visual
{
public:
  Visual();
  ~Visual();

  void find_chip();
  void scan_focus();

private:
  cv::VideoCapture cam;

};

#endif