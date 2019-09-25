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

  struct ChipResult{
    double x;
    double y;
    double area;
    double maxmeas;
    int poly_x1 ;
    int poly_x2 ;
    int poly_x3 ;
    int poly_x4 ;
    int poly_y1 ;
    int poly_y2 ;
    int poly_y3 ;
    int poly_y4 ;
  };

  ChipResult find_chip( const bool );
  double sharpness( const bool );

  void save_frame( const std::string& filename );

  unsigned frame_width() const ;
  unsigned frame_height() const;

  int blur_range;
  int lumi_cutoff;
  int size_cutoff;
  double threshold;
  double ratio_cutoff;
  double poly_range;

private:
  cv::VideoCapture cam;
  void getImg( cv::Mat& );
  void init_var_default();

  // Private methods for easier image processing
  typedef std::vector<cv::Point> Contour_t;
  typedef std::vector<Contour_t> ContourList;
  std::vector<Contour_t> GetContours( cv::Mat& ) const ;
  double GetImageLumi( const cv::Mat&, const Contour_t& ) const;

  Contour_t GetConvexHull( const Contour_t& ) const ;
  Contour_t GetPolyApprox( const Contour_t& ) const ;
  double    GetContourSize( const Contour_t& ) const ;
  double    GetContourMaxMeasure( const Contour_t&) const ;

  void ShowFindChip(
    const cv::Mat&,
    const ContourList&,
    const ContourList&,
    const ContourList&,
    const ContourList& ) const;

  static bool CompareContourSize( const Contour_t&, const Contour_t& );
};

#endif
