#include "logger.hpp"
#include "visual.hpp"

#include <boost/format.hpp>
#include <opencv2/imgproc.hpp>

#include <chrono>
#include <thread>

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
}


// Helper objects for consistant display
static const cv::Scalar red( 100, 100, 255 );
static const cv::Scalar white( 255, 255, 255 );



static bool      check_rectangle( const std::vector<cv::Point>& cont );
static cv::Point average( const std::vector<cv::Point>& cont );

void
Visual::find_chip()
{
  cv::Mat img, gray_img, cont_img;
  std::vector<std::vector<cv::Point> > contours;
  std::vector<std::vector<cv::Point> > recconts;
  std::vector<cv::Vec4i> hierarchy;

  cv::namedWindow( "orig" );
  cv::namedWindow( "proc" );

  while( 1 ){
    cam >> img;
    cv::cvtColor( img, gray_img, cv::COLOR_BGR2GRAY );

    cv::GaussianBlur( gray_img, gray_img, cv::Size( 7, 7 ), 1.5, 1.5 );
    cv::Canny( gray_img, gray_img, 0, 30, 3 );
    cv::findContours( gray_img, contours, hierarchy,
      cv::RETR_TREE, cv::CHAIN_APPROX_SIMPLE, cv::Point( 0, 0 ) );

    for( auto& cont : contours ){
      cv::approxPolyDP( cont, cont, 5, true );
    }

    cont_img = cv::Mat::zeros( gray_img.size(), img.type() );

    recconts.clear();

    for( unsigned i = 0; i < contours.size(); i++ ){

      const cv::Scalar col = check_rectangle( contours.at( i ) ) ? red : white;
      if( check_rectangle( contours.at( i ) ) ){
        recconts.push_back( contours.at( i ) );
      }

      drawContours( cont_img, contours, i, col, 2, 8, hierarchy, 0, cv::Point() );

    }

    if( cv::waitKey( 30 ) >= 0 ){ break;}

    std::string result = (
      boost::format( "Found [%u] rectangles: " )%recconts.size() ).str();

    for( const auto cont : recconts ){
      result += ( boost::format( " (%d,%d)" )
                  % ( average( cont ).x ) %( average( cont ).y )
                  ).str();
    }

    update( GREEN( "[FINDCHIP]" ), result );

    cv::imshow( "orig", img );
    cv::imshow( "proc", cont_img );
  }

  cv::destroyAllWindows();
  return;
}


static bool
check_rectangle( const std::vector<cv::Point>& cont )
{
  if( cont.size() != 4 ){ return false; }
  static const double sumcheck = 0.2;
  static const double dotcheck = 0.3;

  const cv::Point vec1 = cont.at( 1 ) - cont.at( 0 );
  const cv::Point vec2 = cont.at( 3 ) - cont.at( 0 );
  const cv::Point vec3 = cont.at( 2 ) - cont.at( 0 );

  if( cv::norm( vec3-( vec1+vec2 ) ) / cv::norm( vec3 ) > sumcheck ){
    return false;
  }
  if( fabs( vec1.ddot( vec2 ) / cv::norm( vec1 ) / cv::norm( vec2 ) ) > dotcheck ){
    return false;
  }
  return true;
}

static cv::Point
average( const std::vector<cv::Point>& cont )
{
  cv::Point ans;

  for( const auto& p : cont ){
    ans += p;
  }

  ans /= double(cont.size() );
  return ans;
}

#include <iostream>

void
Visual::scan_focus()
{
  static const unsigned FRAME_WIDTH  = 1280;
  static const unsigned FRAME_HEIGHT = 1024;
  static const unsigned FRAME_COUNT  = 10;
  static const std::string WIN_NAME  = "FOCUS_SCAN";

  // Additional camera settings
  cam.set( cv::CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH  );
  cam.set( cv::CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT );

  // Image containers
  cv::Mat img, gray_temp, gray_img;
  cv::Mat work_img, lap_img;

  // Variable containers
  cv::Scalar mu, sigma;
  double max_lap = 0, current_lap;
  unsigned max_pos = 0;

  // Creating display window:
  cv::namedWindow( WIN_NAME,  1 );

  // Getting an average of frames
  gray_img = cv::Mat::zeros( FRAME_HEIGHT, FRAME_WIDTH, CV_64F );

  for( unsigned i = 0; i < FRAME_COUNT; ++i ){
    cam >> img;
    cv::cvtColor( img, gray_temp, cv::COLOR_BGR2GRAY );
    cv::accumulate( gray_temp, gray_img );
    std::this_thread::sleep_for( // Sleeping between frames
      std::chrono::milliseconds( int(1e3/cam.get( cv::CAP_PROP_FPS ) ) +1 )
      );
  }

  gray_img /= FRAME_COUNT;

  // Scanning over rectangular window
  for( unsigned i = 0; i < FRAME_WIDTH - FRAME_WIDTH/8; ++i ){

    gray_temp = gray_img(
      cv::Rect( i, FRAME_HEIGHT/4, FRAME_WIDTH/8, FRAME_HEIGHT/2 ) );
    gray_temp.copyTo( work_img );
    cv::Laplacian( work_img, lap_img, CV_64F, 5 );
    cv::meanStdDev( lap_img, mu, sigma );
    current_lap = sigma.val[0] * sigma.val[0];

    if( current_lap > max_lap ){
      max_lap = current_lap;
      max_pos = i;
    }
    update( GREEN( "[FOCUS-SCAN]" ),
      ( boost::format( "Laplacian current/max: %.2lf/%.2lf (%d/%d)" )
        % current_lap % max_lap % i % max_pos ).str() );

    // Display for debugging
    gray_temp.convertTo( gray_temp, CV_8U );
    gray_temp = gray_img;
    gray_temp.convertTo( gray_temp, CV_8U );
    cv::rectangle( gray_temp,
      cv::Point( i, FRAME_HEIGHT/4 ), cv::Point( i+FRAME_WIDTH/8, FRAME_HEIGHT*3/4 ),
      white,
      2 );
    cv::putText( gray_temp,
      ( boost::format( "%d (%.2lf)" ) % i % current_lap ).str(),
      cv::Point( i, FRAME_HEIGHT/4 ),
      cv::FONT_HERSHEY_SIMPLEX,
      1,
      white
      );
    cv::putText( gray_temp,
      ( boost::format( "%d (%.2lf)" ) % max_pos % max_lap ).str(),
      cv::Point( 50, FRAME_HEIGHT*3/4+100 ),
      cv::FONT_HERSHEY_SIMPLEX,
      1,
      white
      );
    cv::imshow( WIN_NAME, gray_temp );
    cv::waitKey( 30 );
  }


  cv::destroyAllWindows();

}
