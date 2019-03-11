/**
 * @file visual.hpp
 * @date 2018-10-26
 */
#ifndef VISUAL_HPP
#define VISUAL_HPP

#include <opencv2/highgui/highgui.hpp>
#include <opencv2/videoio.hpp>

class Visual
{
public:
  Visual();
  ~Visual();
  Visual( const std::string& );

  void init_dev( const std::string& );
  std::string dev_path;

  std::pair<double,double> find_chip( const bool );
  double sharpness( const bool );

  void save_frame( const std::string& filename );

  unsigned frame_width() const ;
  unsigned frame_height() const;

private:
  cv::VideoCapture cam;
  void getImg( cv::Mat& );
};

#endif
