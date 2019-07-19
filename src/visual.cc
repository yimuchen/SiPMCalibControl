#include "logger.hpp"
#include "visual.hpp"

#include <opencv2/imgproc.hpp>

#include <chrono>
#include <thread>

// Helper objects for consistant display
static const cv::Scalar red( 100, 100, 255 );
static const cv::Scalar white( 255, 255, 255 );


Visual::Visual() : cam(){}
Visual::~Visual(){}

Visual::Visual( const std::string& dev ) : cam()
{
  init_dev( dev );
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
  // Magic numbers that will need some method of adjustment
  static const cv::Size blursize( 5, 5 );
  static const int minthreshold   = 60;
  static const int maxthreshold   = 255;// this doesn't need to change.
  static const double maxchiplumi = 40;
  static const int minchipsize    = 50;
  static const double chipratio   = 1.4;

  // Drawing variables
  static const std::string winname = "FINDCHIP_MONITOR";
  char msg[1024];

  // Operational variables
  cv::Mat img, gray_img;
  std::vector<std::vector<cv::Point> > contours;
  std::vector<std::vector<cv::Point> > hulls;
  std::vector<cv::Vec4i> hierarchy;

  // Getting image
  getImg( img );

  // Standard image processing.
  cv::cvtColor( img, gray_img, cv::COLOR_BGR2GRAY );
  cv::blur( gray_img, gray_img, blursize );
  cv::threshold( gray_img, gray_img,
    minthreshold, maxthreshold,
    cv::THRESH_BINARY );
  cv::findContours( gray_img, contours, hierarchy,
    cv::RETR_TREE, cv::CHAIN_APPROX_SIMPLE, cv::Point( 0, 0 ) );

  // Calculating all contour properties
  for( unsigned i = 0; i < contours.size(); i++ ){
    // Size and dimesion estimation from bounding rectangle
    const cv::Rect bound = cv::boundingRect( contours.at( i ) );
    const double ratio   = (double)bound.height / (double)bound.width;
    const double size    = std::max( bound.height, bound.width );
    if( size < minchipsize ){ continue; }// skipping small speckles
    if( ratio > chipratio
        || ratio < 1./chipratio ){ continue; }// skipping non-square stuff

    // Calculating average color of inside contour
    cv::Mat mask = cv::Mat::zeros( img.size(), CV_8UC1 );
    cv::drawContours( mask, contours, i, 255, cv::FILLED );
    const cv::Scalar meancol = cv::mean( img, mask );
    const double lumi        = 0.2126*meancol[0]
                               + 0.7152*meancol[1]
                               + 0.0722*meancol[2];

    // Selection criteria
    if( lumi > maxchiplumi ){ continue; }// Photosensors are dark.

    // Generating convect hull
    std::vector<cv::Point> hull;
    cv::convexHull( cv::Mat( contours.at( i ) ), hull );

    // Only keeping largest convex hull
    if( !hulls.empty() ){
      const cv::Rect boundprev = cv::boundingRect( hulls.back() );
      const cv::Rect boundpres = cv::boundingRect( hull );

      if( boundpres.height * boundpres.width
          > boundprev.height * boundprev.width ){
        hulls.pop_back();
      }
    }

    hulls.push_back( hull );
  }

  // Calculating convexhull position if nothing is found
  Visual::ChipResult ans;
  if( hulls.empty() ){
    ans = ChipResult{ -1, -1, 0, 0 };
  } else {
    // position calculation of final contour
    cv::Moments m = cv::moments( hulls.at( 0 ), false );

    // Maximum distance in contour
    double distmax = 0;

    for( const auto& p1 : hulls.at( 0 ) ){
      for( const auto& p2 : hulls.at( 0 ) ){
        distmax = std::max( distmax, cv::norm( p2-p1 ) );
      }
    }

    ans = ChipResult{ m.m10/m.m00, m.m01/m.m00,  m.m00, distmax};
  }

  // Plotting final calculation results
  if( monitor ){
    // Window will be created, if already exists, this function does nothing
    cv::namedWindow( winname, cv::WINDOW_AUTOSIZE );

    // Generating the image
    cv::Mat display( img );

    for( unsigned i = 0; i < contours.size(); ++i ){
      cv::drawContours( display, contours, i, white, 2 );
    }

    if( hulls.empty() ){
      cv::putText( display, "NOT FOUND",
        cv::Point( 50, 100 ),
        cv::FONT_HERSHEY_SIMPLEX,
        1, white );
    } else {
      sprintf( msg, "x:%.1lf y:%.1lf", ans.x, ans.y ),
      cv::drawContours( display, hulls, 0, red, 3 );
      cv::circle( display, cv::Point( ans.x, ans.y ), 3, red, cv::FILLED );
      cv::putText( display, msg,
        cv::Point( 50, 100 ),
        cv::FONT_HERSHEY_SIMPLEX,
        2, white );
    }
    imshow( winname, display );
    cv::waitKey( 30 );
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
  .def_readonly( "dev_path", &Visual::dev_path )
  ;
  // Required for coordinate caluclation
  boost::python::class_<Visual::ChipResult>( "ChipResult" )
  .def_readwrite( "x",       &Visual::ChipResult::x )
  .def_readwrite( "y",       &Visual::ChipResult::y )
  .def_readwrite( "area",    &Visual::ChipResult::area )
  .def_readwrite( "maxmeas", &Visual::ChipResult::maxmeas )
  ;
}
