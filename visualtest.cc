#include "opencv2/highgui/highgui.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include <iostream>
#include <stdio.h>
#include <stdlib.h>

int thresh     = 100;
int max_thresh = 255;

/// Function header
void thresh_callback( int, void* );

/** @function main */
int
main( int argc, char** argv )
{
  cv::Mat original = cv::imread( argv[1], 1 );
  cv::Mat orig_gray;
  /// Convert image to gray and blur it
  cv::cvtColor( original, orig_gray, cv::COLOR_BGR2GRAY );
  cv::blur( orig_gray, orig_gray, cv::Size( 3, 3 ) );

  // Create Window
  char* source_window = "Source";
  cv::namedWindow( source_window, cv::WINDOW_AUTOSIZE );
  cv::imshow( source_window, original );

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

  for( int i = 0; i < contours.size(); i++ ){
    const cv::Scalar color( 255, 100,100 );
    cv::drawContours( drawing,
      contours, i,
      color, 2, 8, hierarchy, 0,
      cv::Point() );
  }

  /// Show in a window
  cv::namedWindow( "Contours", cv::WINDOW_AUTOSIZE );
  cv::imshow( "Contours", drawing );

  cv::waitKey( 0 );
  return 0;
}
