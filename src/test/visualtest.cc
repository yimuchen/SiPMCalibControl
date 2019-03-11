#include "opencv2/highgui/highgui.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include <iostream>
#include <stdio.h>
#include <stdlib.h>

int thresh     = 100;
int max_thresh = 255;

/** @function main */
int
main( int argc, char** argv )
{
  cv::Mat original = cv::imread( argv[1], 1 );
  cv::Mat orig_gray;
  /// Convert image to gray and blur it
  cv::cvtColor( original, orig_gray, cv::COLOR_BGR2GRAY );
  cv::blur( orig_gray, orig_gray, cv::Size( 5, 5 ) );
  cv::threshold( orig_gray, orig_gray, 150, 255, cv::THRESH_BINARY );

  // Create Window
  cv::namedWindow( "Source", cv::WINDOW_AUTOSIZE );
  cv::imshow( "Source", original );

  cv::Mat canny_output;
  std::vector<std::vector<cv::Point> > contours;
  std::vector<cv::Vec4i> hierarchy;

  /// Detect edges using canny
  cv::Canny( orig_gray, canny_output, thresh, thresh*2, 3 );
  /// Find contours
  cv::findContours(
    canny_output,
    contours,
    hierarchy,
    cv::RETR_TREE,
    cv::CHAIN_APPROX_SIMPLE,
    cv::Point( 0, 0 ) );

  /// Draw contours
  cv::Mat drawing = cv::Mat::zeros( canny_output.size(), CV_8UC3 );

  for( unsigned i = 0; i < contours.size(); i++ ){
    const cv::Scalar typical( 100, 100,100 );
    const cv::Scalar diodecand( 255,100,100);
    const cv::Rect   bound = cv::boundingRect( contours.at(i) );

    cv::Mat mask = cv::Mat::zeros( original.size() , CV_8UC1 );
    cv::drawContours( mask, contours, i, 255, cv::FILLED );

    const cv::Scalar meancol    = cv::mean( original, mask );

    const double lumi = 0.2126*meancol[0]
                        + 0.7152*meancol[1]
                        + 0.0722*meancol[2];

    const double ratio = (double)bound.height / (double)bound.width;

    const double size = std::max( bound.height, bound.width );

    const double isdiode = (ratio < 1.5 && ratio > 0.66) &&
                           (size > 10 ) && // Avoiding speckles
                           (lumi < 100);

    const cv::Scalar& plotcol = isdiode ? diodecand : typical;
    cv::drawContours( drawing,
      contours, i,
      plotcol,
      2, 8, hierarchy, 0,
      cv::Point() );
  }
  cv::imwrite( "test.jpg", drawing );

  /// Show in a window
  cv::namedWindow( "Contours", cv::WINDOW_AUTOSIZE );
  cv::imshow( "Contours", drawing );


  cv::waitKey( 0 );
  return 0;
}
