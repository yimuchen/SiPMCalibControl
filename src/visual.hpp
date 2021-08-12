#ifndef VISUAL_HPP
#define VISUAL_HPP

#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/videoio.hpp>

// #include <pybind11/numpy.h>

#include <atomic>
#include <memory>
#include <thread>

/**
 * @brief This will be the one class that we will note be declaring as a
 * singleton instance, as we will potentially be using more than 1 camera.
 */
class Visual
{
public:
  Visual();
  ~Visual();
  Visual( const std::string& );

  // Private methods for easier image processing
  typedef std::vector<cv::Point> Contour_t;
  typedef std::vector<Contour_t> ContourList;

  void init_dev( const std::string& );
  std::string dev_path;

  struct VisResult
  {
    double x;
    double y;
    double sharpness_m2;
    double sharpness_m4;
    double area;
    double maxmeas;
    int    poly_x1;
    int    poly_x2;
    int    poly_x3;
    int    poly_x4;
    int    poly_y1;
    int    poly_y2;
    int    poly_y3;
    int    poly_y4;
  };

  unsigned  FrameWidth() const;
  unsigned  FrameHeight() const;
  VisResult GetVisResult();
  cv::Mat   GetImage( const bool );
  bool      SaveImage( const std::string&,
                       const bool raw );
  std::vector<uchar> GetImageBytes();

  int blur_range;
  int lumi_cutoff;
  int size_cutoff;
  double threshold;
  double ratio_cutoff;
  double poly_range;

  // Making the image processing function public to allow for debugging images to
  // be passed through
  std::vector<ContourList> FindContours( const cv::Mat& ) const;
  VisResult                MakeResult( const cv::Mat&, const Contour_t& ) const;
  cv::Mat                  MakeDisplay( const cv::Mat&,
                                        const std::vector<ContourList>& ) const;

private:
  cv::VideoCapture cam;
  cv::Mat image;
  cv::Mat display;
  VisResult latest;

  // Variables for storing the thread handling
  std::thread loop_thread;
  std::atomic<bool> run_loop;
  std::mutex loop_mutex;

  // Function for thread handling;
  void StartLoopThread();
  void EndLoopThread();
  void RunMainLoop( std::atomic<bool>& );

  // Helper function for
  void InitVarDefault();

  // Image processing function
  VisResult FindDetector( const cv::Mat& );

public:
  ContourList GetRawContours( const cv::Mat& ) const;
  Contour_t   GetConvexHull( const Contour_t& ) const;
  Contour_t   GetPolyApprox( const Contour_t& ) const;

  double                    GetImageLumi( const cv::Mat&, const Contour_t& ) const;
  std::pair<double, double> sharpness( const cv::Mat&, const cv::Rect& ) const;
  double                    GetContourSize( const Contour_t& ) const;
  double                    GetContourMaxMeasure( const Contour_t& ) const;


  static bool CompareContourSize( const Contour_t&, const Contour_t& );
};

#endif
