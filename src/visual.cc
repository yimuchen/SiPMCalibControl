#include "visual.hpp"

// Additional opencv stuff
#include <opencv2/core/utils/logger.hpp>

// Helper objects for consistant display (format BGR)
static const cv::Scalar red( 100, 100, 255 );
static const cv::Scalar cyan( 255, 255, 100 );
static const cv::Scalar yellow( 100, 255, 255 );
static const cv::Scalar green( 100, 255, 100 );
static const cv::Scalar white( 255, 255, 255 );

// Setting OPENCV into silent mode
static const auto __dummy_settings
  = cv::utils::logging::setLogLevel( cv::utils::logging::LOG_LEVEL_SILENT );


Visual::Visual() :
  cam(),
  run_loop( false )
{
  init_var_default();
  // Py_Initialize();
  // boost::python::numpy::initialize();
  start_thread();
}

Visual::Visual( const std::string& dev ) :
  cam(),
  run_loop( false )
{
  init_dev( dev );
  init_var_default();

  start_thread();
}

void
Visual::init_dev( const std::string& dev )
{
  end_thread();
  dev_path = dev;
  cam.release();
  cam.open( dev_path );
  if( !cam.isOpened() ){// check if we succeeded
    throw std::runtime_error( "Cannot open webcam" );
  }
  // Additional camera settings
  cam.set( cv::CAP_PROP_FRAME_WIDTH,  1280 );
  cam.set( cv::CAP_PROP_FRAME_HEIGHT, 1024 );
  cam.set( cv::CAP_PROP_BUFFERSIZE,   1 );// Reducing buffer for fast capture
  cam.set( cv::CAP_PROP_SHARPNESS,    0 );// disable postprocess sharpening.

  start_thread();
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

Visual::~Visual()
{
  printf( "Ending the visual thread\n" );
  end_thread();
  printf( "Closing visual system interfaces\n" );
  cam.release();
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

/**
 * @brief Facility for running the image processing thread
 */
void
Visual::start_thread()
{
  run_loop    = true;
  loop_thread = std::thread( [this] {
    this->RunMainLoop( std::ref( run_loop ) );
  } );
}

void
Visual::end_thread()
{
  if( run_loop == true ){
    run_loop = false;
    loop_thread.join();
  }
}

void
Visual::RunMainLoop( std::atomic<bool>& run_loop )
{
  namespace st = std::chrono;
  auto get_time = []( void )->size_t {
                    return st::duration_cast<st::microseconds>(
                      st::high_resolution_clock::now().time_since_epoch()
                      ).count();
                  };

  while( run_loop == true ){
    const size_t time_start = get_time();
    size_t time_end         = get_time();

    loop_mutex.lock();

    do {
      cam >> image;
    } while( ( image.empty() || image.cols == 0 ) && cam.isOpened() );

    latest = find_det( image );
    loop_mutex.unlock();

    while( time_end - time_start < 5e3 ){
      // Updating at 2000fps. Must be faster than the webcam refresh rate for
      // realtime image over internet
      std::this_thread::sleep_for( st::milliseconds( 1 ) );
      time_end = get_time();
    }
  }
}


Visual::VisResult
Visual::find_det( const cv::Mat& img )
{
  static const VisResult empty_return = VisResult { -1, -1, 0, 0, 0,
                                                    0, 0, 0, 0,
                                                    0, 0, 0, 0 };

  // Early exits if
  if( img.empty() || img.cols == 0 ){
    return empty_return;
  }

  const auto contours = find_contours( img );
  const auto& hulls   = contours.at( 0 );

  const auto ans = hulls.empty() ? empty_return :
                   make_result( img, hulls.at( 0 ) );
  display = make_display( img, contours );
  return ans;
}

/**
 * @brief Given an base image, find the contours and group them according to the
 * various selection criteria.
 */
std::vector<Visual::ContourList>
Visual::find_contours( const cv::Mat& img ) const
{
  const ContourList contours = GetRawContours( img );
  ContourList failed_ratio;
  ContourList failed_lumi;
  ContourList failed_rect;
  ContourList hulls;

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
    const double lumi = GetImageLumi( image, contours.at( i ) );
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

  // Sorting candidates according to contour size
  std::sort( hulls.begin(), hulls.end(), Visual::CompareContourSize );

  return { hulls,
           failed_rect,
           failed_lumi,
           failed_ratio };
}

Visual::VisResult
Visual::make_result( const cv::Mat& img, const Visual::Contour_t& hull ) const
{
  // position calculation of final contour
  const cv::Moments m = cv::moments( hull, false );

  // Maximum distance in contour
  const double distmax        = GetContourMaxMeasure( hull );
  const Contour_t poly        = GetPolyApprox( hull );
  const cv::Rect bound        = cv::boundingRect( hull );
  const cv::Rect double_bound = cv::Rect( bound.x - bound.width /2
                                        , bound.y - bound.height/2
                                        , bound.width*2
                                        , bound.height*2 );
  const auto p = sharpness( img, double_bound );

  return VisResult {
    m.m10/m.m00, m.m01/m.m00,
    p.second,
    p.first,
    m.m00, distmax,
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

cv::Mat
Visual::make_display( const cv::Mat&                          img,
                      const std::vector<Visual::ContourList>& contlist ) const
{
  // Drawing variables
  char msg[1024];
  cv::Mat ret = img.clone();

  auto PlotContourList = [this, &ret]( const Visual::ContourList& list,
                                       const cv::Scalar& color ) -> void {
                           for( unsigned i = 0; i < list.size(); ++i ){
                             cv::drawContours( ret, list, i, color );
                           }
                         };

  auto PlotText = [this, &ret]( const std::string& str,
                                const cv::Point& pos,
                                const cv::Scalar& col ) -> void {
                    cv::putText( ret, str,
                      pos, cv::FONT_HERSHEY_SIMPLEX, 0.8, col, 2 );
                  };


  PlotContourList( contlist.at( 0 ), cyan   );
  PlotContourList( contlist.at( 1 ), white );
  PlotContourList( contlist.at( 2 ), green );
  PlotContourList( contlist.at( 3 ), yellow );

  // Plotting the final results
  if( contlist.at( 0 ).empty() ){
    PlotText( "NOT FOUND", cv::Point( 20, 20 ), red );
  } else {
    const auto res = make_result( img, contlist.at( 0 ).at( 0 ) );
    const double x = res.x;
    const double y = res.y;
    const double s2 = res.sharpness_m2;
    const double s4 = res.sharpness_m4;

    sprintf( msg, "x:%.1lf y:%.1lf s2:%.2lf s4:%.2lf", x, y, s2, s4 ),
    cv::drawContours( ret, contlist.at( 0 ), 0, red, 3 );
    cv::circle( ret, cv::Point( x, y ), 3, red, cv::FILLED );
    PlotText( msg, cv::Point( 20, 20 ), red );
  }

  return ret;
}

std::vector<Visual::Contour_t>
Visual::GetRawContours( const cv::Mat& img ) const
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
  // Expecting the internals of the photosensor to be dark.
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

  return x_bound.area() > y_bound.area();
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

std::pair<double,double>
Visual::sharpness( const cv::Mat& img, const cv::Rect& crop ) const
{
  // Image containers
  cv::Mat cimg[3], bimg, fimg, lap;

  // Variable containers
  cv::Scalar mu, sigma;

  // Convert original image to gray scale
  cv::cvtColor( img, bimg, cv::COLOR_BGR2GRAY );

  // Getting green channel image image converting to gray scale cv::split( img,
  // cimg ); cimg[1].convertTo( fimg, CV_32FC1 );

  // Creating the crops
  if( crop.width == 0 || crop.height == 0 ){
    return std::pair<double,double>(0,0);
  }

  // Cropping to range sometimes is bad... not sure why just yet
  try {
    bimg = bimg( crop ).clone();
  } catch( cv::Exception& e ){
    return std::pair<double,double>(0,0);
  }

  cv::blur( bimg, bimg, cv::Size( 2, 2 ) );

  // Calculating lagrangian
  cv::Laplacian( bimg, lap, CV_64F, 5 );

  // Calculating the 2nd and 4th moment
  mu = cv::mean( lap );
  double mo2 = 0, mo4 = 0;

  for( int r = 0; r < lap.rows; ++r ){
    for( int c = 0; c < lap.cols; ++c ){
      const double val  = lap.at<double>( r, c );
      const double diff = val - mu.val[0];
      mo2 += diff * diff;
      mo4 += diff * diff * diff * diff;
    }
  }

  //
  mo2 /= lap.rows * lap.cols;
  mo4 /= lap.rows * lap.cols;

  return std::pair<double,double>( mo4 / (mo2*mo2), mo2 );
}

Visual::VisResult
Visual::get_result()
{
  loop_mutex.lock();
  VisResult ans = latest;
  loop_mutex.unlock();
  return ans;
}

bool
Visual::save_image( const std::string& path, bool raw )
{
  const cv::Mat mat = get_image( raw );
  cv::imwrite( path, mat );
  return true;
}


cv::Mat
Visual::get_image( const bool raw )
{
  static const cv::Mat blank_frame(
    cv::Size( frame_width(), frame_height() ),
    CV_8UC3, cv::Scalar( 0, 0, 0 ) );

  loop_mutex.lock();
  cv::Mat ans_mat = ( display.empty() || display.cols == 0 ) ? blank_frame :
                    raw ? image :
                    display;
  loop_mutex.unlock();

  return ans_mat;
}

PyObject*
Visual::get_image_bytes()
{
  // Returning the image generated from the detection algorithm as a byte
  // sequence to be returned by a HTTP image request.
  std::vector<uchar> buf;// Storage required by opencv.
  cv::imencode( ".jpg", get_image( false ), buf );

  // Conversion of bytes sequence to python objects
  // https://www.auctoris.co.uk/2017/12/21/
  // advanced-c-python-integration-with-boost-python-part-2
  return PyBytes_FromObject(
    PyMemoryView_FromMemory( (char*)buf.data(), buf.size(), PyBUF_READ ) );
}
