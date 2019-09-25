#include "logger.hpp"
#include "visual.hpp"

#include <opencv2/core/utils/logger.hpp>
#include <opencv2/imgproc.hpp>

#include <chrono>
#include <thread>

// Helper objects for consistant display BGR
static const cv::Scalar red( 100, 100, 255 );
static const cv::Scalar cyan( 255, 255, 100 );
static const cv::Scalar yellow( 100, 255, 255 );
static const cv::Scalar green( 100, 255, 100 );
static const cv::Scalar white( 255, 255, 255 );

// Setting OPENCV into silent mode
static const auto __dummy_settings
  = cv::utils::logging::setLogLevel( cv::utils::logging::LOG_LEVEL_SILENT );


Visual::Visual() : cam()
{
  init_var_default();
}

Visual::Visual( const std::string& dev ) : cam()
{
  init_dev( dev );
  init_var_default();
}

void
Visual::init_dev( const std::string& dev )
{
  dev_path = dev;
  cam.release();
  cam.open( dev_path );
  if( !cam.isOpened() ){// check if we succeeded
    throw std::runtime_error( "Cannot open webcam" );
  }
  // Additional camera settings
  cam.set( cv::CAP_PROP_FRAME_WIDTH,  1280 );
  cam.set( cv::CAP_PROP_FRAME_HEIGHT, 1024 );
  cam.set( cv::CAP_PROP_BUFFERSIZE,      1 );// Reducing buffer for fast capture
}

void
Visual::init_var_default()
{
  threshold    = 80;
  blur_range   = 5;
  lumi_cutoff  = 40;
  size_cutoff  = 50;
  ratio_cutoff = 1.4;
  poly_range   = 0.08;
}

Visual::~Visual(){}

unsigned
Visual::frame_width() const
{
  return cam.get( cv::CAP_PROP_FRAME_WIDTH );
}

unsigned
Visual::frame_height() const
{
  return cam.get( cv::CAP_PROP_FRAME_HEIGHT );
}

Visual::ChipResult
Visual::find_chip( const bool monitor )
{
  // Operational variables
  cv::Mat img;
  // Getting image
  getImg( img );


  const std::vector<Contour_t> contours = GetContours( img );

  std::vector<Contour_t> failed_ratio;
  std::vector<Contour_t> failed_lumi;
  std::vector<Contour_t> failed_rect;
  std::vector<Contour_t> hulls;

  // Calculating all contour properties
  for( unsigned i = 0; i < contours.size(); i++ ){
    const double size = GetContourSize( contours.at( i ) );
    if( size < size_cutoff ){ continue; }// skipping small speckles

    // Expecting the ratio of the bounding box to be square.
    const cv::Rect bound = cv::boundingRect( contours.at( i ) );
    const double ratio   = (double)bound.height / (double)bound.width;
    if( ratio > ratio_cutoff || ratio < 1./ratio_cutoff ){
      failed_ratio.push_back( contours.at( i ) );
      continue;
    }

    // Expecting the internals of of the photosensor to be dark.
    const double lumi = GetImageLumi( img, contours.at( i ) );
    if( lumi > lumi_cutoff ){
      failed_lumi.push_back( contours.at( i ) );
      continue;
    }// Photosensors are dark.

    // Generating convex hull
    const Contour_t hull = GetConvexHull( contours.at( i ) );
    const Contour_t poly = GetPolyApprox( hull );
    if( poly.size() != 4 ){
      failed_rect.push_back( contours.at( i ) );
      continue;
    }

    hulls.push_back( hull );
  }

  std::sort( hulls.begin(), hulls.end(), Visual::CompareContourSize );

  if( monitor ){
    ShowFindChip( img, failed_ratio, failed_lumi, failed_rect, hulls );
  }

  if( hulls.empty() ){
    return ChipResult{ -1, -1, 0, 0,
                       0, 0, 0, 0,
                       0, 0, 0, 0 };
  } else {
    // position calculation of final contour
    const cv::Moments m = cv::moments( hulls.at( 0 ), false );

    // Maximum distance in contour
    const double distmax = GetContourMaxMeasure( hulls.at( 0 ) );
    const Contour_t poly = GetPolyApprox( hulls.at( 0 ) );

    return ChipResult{
      m.m10/m.m00, m.m01/m.m00,  m.m00, distmax,
      poly.at( 0 ).x,
      poly.at( 1 ).x,
      poly.at( 2 ).x,
      poly.at( 3 ).x,
      poly.at( 0 ).y,
      poly.at( 1 ).y,
      poly.at( 2 ).y,
      poly.at( 3 ).y,
    };
  }
}

void
Visual::ShowFindChip(
  const cv::Mat&     img,
  const ContourList& failed_ratio,
  const ContourList& failed_lumi,
  const ContourList& failed_rect,
  const ContourList& hulls  ) const
{
  // Drawing variables
  static const std::string winname = "FINDCHIP_MONITOR";
  char msg[1024];

  // Window will be created, if already exists, this function does nothing
  cv::namedWindow( winname, cv::WINDOW_AUTOSIZE );

  // Generating the image
  cv::Mat display( img );

  auto PlotContourList = [&display]( const ContourList& list,
                                     const cv::Scalar& color ) -> void {
                           for( unsigned i = 0; i < list.size(); ++i ){
                             cv::drawContours( display, list, i, color );
                           }
                         };

  auto PlotText = [&display]( const std::string& str,
                              const cv::Point& pos,
                              const cv::Scalar& col ) -> void {
                    cv::putText( display, str,
                      pos, cv::FONT_HERSHEY_SIMPLEX, 0.8, col, 2 );
                  };

  PlotContourList( failed_ratio, white );
  PlotText( "Failed Ratio", cv::Point(50,700), white );

  PlotContourList( failed_lumi,  green );
  PlotText( "Failed Lumi", cv::Point(50,750), green );

  PlotContourList( failed_rect, yellow );
  PlotText( "Failed Rect", cv::Point(50,800), yellow );

  PlotContourList( hulls,         cyan );
  PlotText( "Candidate", cv::Point( 50, 850 ), cyan );

  if( hulls.empty() ){
    PlotText( "NOT FOUND", cv::Point( 20,20), red );
  } else {
    const cv::Moments m = cv::moments( hulls.at( 0 ), false );
    const double x      = m.m10/m.m00;
    const double y      = m.m01/m.m00;

    sprintf( msg, "x:%.1lf y:%.1lf", x, y ),
    cv::drawContours( display, hulls, 0, red, 3 );
    cv::circle( display, cv::Point( x, y ), 3, red, cv::FILLED );
    PlotText( msg, cv::Point( 50, 100 ), red );
  }

  imshow( winname, display );
  cv::waitKey( 30 );
}

std::vector<Visual::Contour_t>
Visual::GetContours( cv::Mat& img ) const
{
  cv::Mat gray_img;
  std::vector<cv::Vec4i> hierarchy;
  std::vector<Contour_t> contours;

  // Standard image processing.
  cv::cvtColor( img, gray_img, cv::COLOR_BGR2GRAY );
  cv::blur( gray_img, gray_img, cv::Size( blur_range, blur_range ) );
  cv::threshold( gray_img, gray_img,
    threshold, 255,
    cv::THRESH_BINARY );
  cv::findContours( gray_img, contours, hierarchy,
    cv::RETR_TREE, cv::CHAIN_APPROX_SIMPLE, cv::Point( 0, 0 ) );

  return contours;
}

double
Visual::GetImageLumi( const cv::Mat& img, const Contour_t& cont ) const
{
  // Expecting the internals of of the photosensor to be dark.
  const std::vector<Contour_t> v_cont = { cont };

  cv::Mat mask = cv::Mat::zeros( img.size(), CV_8UC1 );

  cv::drawContours( mask, v_cont, 0, 255, cv::FILLED );

  const cv::Scalar meancol = cv::mean( img, mask );

  return 0.2126*meancol[0]
         + 0.7152*meancol[1]
         + 0.0722*meancol[2];
}

bool
Visual::CompareContourSize( const Contour_t& x, const Contour_t& y )
{
  const cv::Rect x_bound = cv::boundingRect( x );
  const cv::Rect y_bound = cv::boundingRect( y );

  return x_bound.height * x_bound.width
         > y_bound.height * y_bound.width;
}

Visual::Contour_t
Visual::GetConvexHull( const Contour_t& x ) const
{
  Contour_t hull;
  cv::convexHull( cv::Mat( x ), hull );
  return hull;
}

Visual::Contour_t
Visual::GetPolyApprox( const Contour_t& x ) const
{
  Contour_t ans;
  const double size = GetContourSize( x );

  cv::approxPolyDP( x, ans, size*poly_range, true );

  return ans;
}

double
Visual::GetContourSize( const Contour_t& x ) const
{
  const cv::Rect bound = cv::boundingRect( x );
  return std::max( bound.height, bound.width );
}

double
Visual::GetContourMaxMeasure( const Contour_t& x ) const
{
  // Maximum distance in contour
  double ans = 0;

  for( const auto& p1 : x ){
    for( const auto& p2 : x ){
      ans = std::max( ans, cv::norm( p2-p1 ) );
    }
  }

  return ans;
}

double
Visual::sharpness( const bool monitor )
{
  // Image containers
  cv::Mat img, lap;

  // Variable containers
  cv::Scalar mu, sigma;

  // Getting image converting to gray scale
  getImg( img );
  cv::cvtColor( img, img, cv::COLOR_BGR2GRAY );

  // Calculating lagrangian.
  cv::Laplacian( img, lap, CV_64F, 5 );
  cv::meanStdDev( lap, mu, sigma );
  return sigma.val[0] * sigma.val[0];
}

void
Visual::getImg( cv::Mat& img )
{
  for( unsigned i = 0; i < 2; ++i ){
    cam >> img;// Flushing multiple frames to image
    std::this_thread::sleep_for(// Sleeping a full capture frame time
      std::chrono::milliseconds( 10 )
      );
  }
}

void
Visual::save_frame( const std::string& filename )
{
  cv::Mat img;
  cam >> img;
  imwrite( filename, img );
}


#include <boost/python.hpp>

BOOST_PYTHON_MODULE( visual )
{
  boost::python::class_<Visual>( "Visual" )
  .def( "init_dev",     &Visual::init_dev )
  .def( "find_chip",    &Visual::find_chip )
  .def( "sharpness",    &Visual::sharpness )
  .def( "save_frame",   &Visual::save_frame )
  .def( "frame_width",  &Visual::frame_width )
  .def( "frame_height", &Visual::frame_height )
  .def_readonly( "dev_path", &Visual::dev_path  )
  .def_readwrite( "threshold",    &Visual::threshold    )
  .def_readwrite( "blur_range",   &Visual::blur_range   )
  .def_readwrite( "lumi_cutoff",  &Visual::lumi_cutoff  )
  .def_readwrite( "size_cutoff",  &Visual::size_cutoff  )
  .def_readwrite( "ratio_cutoff", &Visual::ratio_cutoff )
  .def_readwrite( "poly_range",   &Visual::poly_range   )
  ;

  // Required for coordinate caluclation
  boost::python::class_<Visual::ChipResult>( "ChipResult" )
  .def_readwrite( "x",       &Visual::ChipResult::x )
  .def_readwrite( "y",       &Visual::ChipResult::y )
  .def_readwrite( "area",    &Visual::ChipResult::area )
  .def_readwrite( "maxmeas", &Visual::ChipResult::maxmeas )
  .def_readwrite( "poly_x1", &Visual::ChipResult::poly_x1 )
  .def_readwrite( "poly_x2", &Visual::ChipResult::poly_x2 )
  .def_readwrite( "poly_x3", &Visual::ChipResult::poly_x3 )
  .def_readwrite( "poly_x4", &Visual::ChipResult::poly_x4 )
  .def_readwrite( "poly_y1", &Visual::ChipResult::poly_y1 )
  .def_readwrite( "poly_y2", &Visual::ChipResult::poly_y2 )
  .def_readwrite( "poly_y3", &Visual::ChipResult::poly_y3 )
  .def_readwrite( "poly_y4", &Visual::ChipResult::poly_y4 )
  ;
}
