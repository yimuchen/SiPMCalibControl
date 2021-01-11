#include "logger.hpp"

#include <opencv2/core/utils/logger.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/videoio.hpp>

#include <boost/python.hpp>
#include <boost/python/numpy.hpp>

#include <atomic>
#include <chrono>
#include <mutex>
#include <thread>

class Visual
{
public:
  Visual();
  ~Visual();
  Visual( const std::string& );

  void init_dev( const std::string& );
  std::string dev_path;

  struct VisResult
  {
    double x;
    double y;
    double sharpness;
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

  unsigned                      frame_width() const;
  unsigned                      frame_height() const;
  VisResult                     get_result();
  boost::python::numpy::ndarray get_image();
  bool                          save_image( const std::string& );
  PyObject*                     get_image_bytes();

  int blur_range;
  int lumi_cutoff;
  int size_cutoff;
  double threshold;
  double ratio_cutoff;
  double poly_range;

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
  void start_thread();
  void end_thread();
  void RunMainLoop( std::atomic<bool>& );

  // Helper function for
  void init_var_default();

  VisResult find_det();

  // Private methods for easier image processing
  typedef std::vector<cv::Point> Contour_t;
  typedef std::vector<Contour_t> ContourList;

  std::vector<Contour_t> GetContours( cv::Mat& ) const;
  Contour_t              GetConvexHull( const Contour_t& ) const;
  Contour_t              GetPolyApprox( const Contour_t& ) const;

  double GetImageLumi( const cv::Mat&, const Contour_t& ) const;
  double sharpness( const cv::Mat&, const cv::Rect& ) const;
  double GetContourSize( const Contour_t& ) const;
  double GetContourMaxMeasure( const Contour_t& ) const;

  void generate_display( const ContourList&,
                         const ContourList&,
                         const ContourList&,
                         const ContourList& );
  cv::Mat get_image_cv();

  static bool CompareContourSize( const Contour_t&, const Contour_t& );
};

// Helper objects for consistant display BGR
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
  boost::python::numpy::initialize();

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
  cam.set( cv::CAP_PROP_BUFFERSIZE,   1 );   // Reducing buffer for fast capture

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
  end_thread();
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
  auto get_time
    = []( void )->size_t {
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
      // Scaling down the image for faster processing.
    } while( ( image.empty() || image.cols == 0 ) && cam.isOpened() );

    latest = find_det();
    loop_mutex.unlock();

    while( time_end - time_start < 5e3 ){
      // Updating at 200fps. Must be faster than the webcam refresh rate for
      // realtime image over internet
      std::this_thread::sleep_for( st::milliseconds( 1 ) );
      time_end = get_time();
    }
  }
}


Visual::VisResult
Visual::find_det()
{
  static const VisResult empty_return = VisResult { -1, -1, 0, 0, 0,
                                                    0, 0, 0, 0,
                                                    0, 0, 0, 0 };

  // Early exits if
  if( image.empty() || image.cols == 0 ){
    return empty_return;
  }

  // Reducing image size to spped up algorithm
  cv::resize( image, image, cv::Size( 0, 0 ), 0.5, 0.5 );

  const ContourList contours = GetContours( image );
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

  std::sort( hulls.begin(), hulls.end(), Visual::CompareContourSize );

  generate_display( failed_ratio, failed_lumi, failed_rect, hulls );


  if( hulls.empty() ){
    return empty_return;
  } else {
    // position calculation of final contour
    const cv::Moments m = cv::moments( hulls.at( 0 ), false );

    // Maximum distance in contour
    const double distmax        = GetContourMaxMeasure( hulls.at( 0 ) );
    const Contour_t poly        = GetPolyApprox( hulls.at( 0 ) );
    const cv::Rect bound        = cv::boundingRect( hulls.at( 0 ) );
    const cv::Rect double_bound = cv::Rect( bound.x - bound.width /2
                                          , bound.y - bound.height/2
                                          , bound.width*2
                                          , bound.height*2 );
    const double sharp = sharpness( image, double_bound );

    return VisResult {
      m.m10/m.m00, m.m01/m.m00,
      sharp,
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
}

void
Visual::generate_display( const ContourList& failed_ratio,
                          const ContourList& failed_lumi,
                          const ContourList& failed_rect,
                          const ContourList& hulls  )
{
  // Drawing variables
  char msg[1024];

  // Generating the image
  display = image;

  auto PlotContourList = [this]( const ContourList& list,
                                 const cv::Scalar& color ) -> void {
                           for( unsigned i = 0; i < list.size(); ++i ){
                             cv::drawContours( this->display, list, i, color );
                           }
                         };

  auto PlotText = [this]( const std::string& str,
                          const cv::Point& pos,
                          const cv::Scalar& col ) -> void {
                    cv::putText( this->display, str,
                      pos, cv::FONT_HERSHEY_SIMPLEX, 0.8, col, 2 );
                  };

  PlotContourList( failed_ratio, white );
  PlotContourList( failed_lumi,  green );
  PlotContourList( failed_rect,  yellow );
  PlotContourList( hulls,        cyan );
  if( hulls.empty() ){
    PlotText( "NOT FOUND", cv::Point( 20, 20 ), red );
  } else {
    const cv::Moments m = cv::moments( hulls.at( 0 ), false );
    const double x      = m.m10/m.m00;
    const double y      = m.m01/m.m00;

    sprintf( msg, "x:%.1lf y:%.1lf", x, y ),
    cv::drawContours( display, hulls, 0, red, 3 );
    cv::circle( display, cv::Point( x, y ), 3, red, cv::FILLED );
    PlotText( msg, cv::Point( 20, 20 ), red );
  }
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

double
Visual::sharpness( const cv::Mat& img, const cv::Rect& crop ) const
{
  // Image containers
  cv::Mat working_image, lap;

  // Variable containers
  cv::Scalar mu, sigma;

  // Getting image converting to gray scale
  cv::cvtColor( img, working_image, cv::COLOR_BGR2GRAY );
  if( crop.width == 0 || crop.height == 0 ){
    return 0;
  }

  // Cropping to range sometimes is bad... not sure why just yet
  try {
    working_image = working_image( crop ).clone();
  } catch( cv::Exception& e ){
    return 0;
  }

  // Calculating lagrangian.
  cv::Laplacian( working_image, lap, CV_64F, 5 );
  cv::meanStdDev( lap, mu, sigma );
  return sigma.val[0] * sigma.val[0];
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
Visual::save_image( const std::string& path )
{
  const cv::Mat mat = get_image_cv();
  cv::imwrite( path, mat );
  return true;
}


cv::Mat
Visual::get_image_cv()
{
  static const cv::Mat blank_frame(
    cv::Size( frame_width(), frame_height() ),
    CV_8UC3, cv::Scalar( 0, 0, 0 ) );

  loop_mutex.lock();
  cv::Mat ans_mat = ( display.empty() || display.cols == 0 ) ? blank_frame :
                    display;
  loop_mutex.unlock();

  return ans_mat;
}

boost::python::numpy::ndarray
Visual::get_image()
{
  cv::Mat mat = get_image_cv();

  namespace bp = boost::python;

  bp::tuple shape = bp::make_tuple( mat.rows
                                  , mat.cols
                                  , mat.channels() );
  bp::tuple stride = bp::make_tuple(
    mat.channels() * mat.cols * sizeof( uchar ),
    mat.channels() * sizeof( uchar ),
    sizeof( uchar ) );

  return bp::numpy::from_data( mat.data
                             , bp::numpy::dtype::get_builtin<uchar>()
                             , shape
                             , stride
                             , bp::object() );
}

PyObject*
Visual::get_image_bytes()
{
  // Returning the image generated from the detection algorithm as a byte
  // sequence to be returned by a HTTP image request.
  std::vector<uchar> buf;// Storage required by opencv.
  cv::Mat mat = get_image_cv();
  cv::imencode( ".jpg", mat, buf );

  // Conversion of bytes sequence to python objects
  // https://www.auctoris.co.uk/2017/12/21/
  // advanced-c-python-integration-with-boost-python-part-2
  return PyBytes_FromObject(
    PyMemoryView_FromMemory( (char*)buf.data(), buf.size(), PyBUF_READ ) );
}

#include <boost/python.hpp>

BOOST_PYTHON_MODULE( visual )
{
  boost::python::class_<Visual, boost::noncopyable>( "Visual" )
  .def( "init_dev",        &Visual::init_dev        )
  .def( "frame_width",     &Visual::frame_width     )
  .def( "frame_height",    &Visual::frame_height    )
  .def( "get_latest",      &Visual::get_result      )
  .def( "get_image",       &Visual::get_image       )
  .def( "get_image_bytes", &Visual::get_image_bytes )
  .def( "save_image",      &Visual::save_image      )
  .def_readonly( "dev_path", &Visual::dev_path  )
  .def_readwrite( "threshold",    &Visual::threshold    )
  .def_readwrite( "blur_range",   &Visual::blur_range   )
  .def_readwrite( "lumi_cutoff",  &Visual::lumi_cutoff  )
  .def_readwrite( "size_cutoff",  &Visual::size_cutoff  )
  .def_readwrite( "ratio_cutoff", &Visual::ratio_cutoff )
  .def_readwrite( "poly_range",   &Visual::poly_range   )
  ;

  // Required for coordinate calculation
  boost::python::class_<Visual::VisResult>( "VisResult" )
  .def_readwrite( "x",         &Visual::VisResult::x         )
  .def_readwrite( "y",         &Visual::VisResult::y         )
  .def_readwrite( "sharpness", &Visual::VisResult::sharpness )
  .def_readwrite( "area",      &Visual::VisResult::area      )
  .def_readwrite( "maxmeas",   &Visual::VisResult::maxmeas   )
  .def_readwrite( "poly_x1",   &Visual::VisResult::poly_x1   )
  .def_readwrite( "poly_x2",   &Visual::VisResult::poly_x2   )
  .def_readwrite( "poly_x3",   &Visual::VisResult::poly_x3   )
  .def_readwrite( "poly_x4",   &Visual::VisResult::poly_x4   )
  .def_readwrite( "poly_y1",   &Visual::VisResult::poly_y1   )
  .def_readwrite( "poly_y2",   &Visual::VisResult::poly_y2   )
  .def_readwrite( "poly_y3",   &Visual::VisResult::poly_y3   )
  .def_readwrite( "poly_y4",   &Visual::VisResult::poly_y4   )
  ;
}
