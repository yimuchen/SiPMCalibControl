#include "logger.hpp"
#include "visual.hpp"

#include <boost/format.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/xphoto.hpp>

Visual::Visual() :
  cam( 0 )// Defaults to /dev/video0
{
  if( !cam.isOpened() ){// check if we succeeded
    throw std::runtime_error( "Did not open webcam" );
  }
  // cv::namedWindow( "orig", 1 );
  // cv::namedWindow( "proc", 1 );
}


Visual::~Visual()
{

}

static bool      check_rectangle( const std::vector<cv::Point>& cont );
static cv::Point average( const std::vector<cv::Point>& cont );

void
Visual::find_chip()
{
  cv::Mat img, gray_img, cont_img;
  std::vector<std::vector<cv::Point> > contours;
  std::vector<std::vector<cv::Point> > recconts;
  std::vector<cv::Vec4i> hierarchy;

  cv::namedWindow( "orig", 1 );
  cv::namedWindow( "proc", 1 );

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
      static const cv::Scalar red( 100, 100, 255 );
      static const cv::Scalar white( 255, 255, 255 );

      const cv::Scalar col = check_rectangle( contours.at( i ) ) ? red : white;
      if( check_rectangle( contours.at( i ) ) ){
        recconts.push_back( contours.at( i ) );
      }

      drawContours( cont_img, contours, i, col, 2, 8, hierarchy, 0, cv::Point() );

    }

    if( cv::waitKey( 30 ) >= 0 ){ break;}

    std::string result = ( boost::format( "Found [%u] rectangles: " )%recconts.size() ).str();

    for( const auto cont : recconts ){
      result += ( boost::format( " (%d,%d)" )
                  % ( average( cont ).x ) %( average( cont ).y )
                  ).str();
    }

    update( GREEN( "[FINDCHIP]" ), result );

    cv::imshow( "orig",      img );
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


void
Visual::scan_focus()
{
  cv::Mat img, gray_img, lap_img;

  //cam.set( CV_CAP_PROP_AUTOFOCUS, false );

  cv::namedWindow( "img", 1 );

  for( ;; ){
    if( cv::waitKey( 30 ) >= 0 ){ break;}
    cam >> img;
    // cam.set( CV_CAP_PROP_FOCUS, i );
    cv::imshow( "img", img );

    cv::cvtColor( img, gray_img, cv::COLOR_BGR2GRAY );

    cv::Laplacian( gray_img, lap_img, CV_64F,5 );
    cv::Scalar mu, sigma;
    cv::meanStdDev( img, mu, sigma );

    double lapvar = sigma.val[0] * sigma.val[0];
    update( GREEN("[FOCUS-SCAN]"),
      ( boost::format( "Laplacian %.2lf (%d)" )%lapvar%110 ).str() );
  }

  cv::destroyAllWindows();

}
