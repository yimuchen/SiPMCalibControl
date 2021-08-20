#include <opencv2/imgcodecs.hpp>

#include <iostream>
#include "visual.hpp"


/**
 * @brief Testing function for image production
 *
 * @return int
 */
int
main( int argc, char* argv[] )
{
  if( argc < 3 ){
    std::cout << "";
    return 1;
  }

  cv::Mat img = cv::imread( argv[1] );
  Visual vis;
  //vis.threshold = 80;
  //vis.lumi_cutoff = 40;
  auto clist = vis.FindContours( img );
  std::cout <<  vis.GetImageLumi(img,clist[0][0]) << std::endl;;
  auto dis = vis.MakeDisplay( img, clist  );

  cv::imwrite( argv[2], dis );

  return 0;
}
