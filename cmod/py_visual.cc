#include "visual.hpp"
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

PYBIND11_MODULE( visual, m )
{
  pybind11::class_<Visual>( m, "Visual" )
  .def( pybind11::init<>() )
  .def( pybind11::init<const std::string&>() )
  .def( "init_dev",      &Visual::init_dev     )
  .def( "frame_width",    &Visual::FrameWidth   )
  .def( "frame_height",   &Visual::FrameHeight  )
  .def( "get_latest",    &Visual::GetVisResult )
  .def( "save_image",     &Visual::SaveImage    )
  .def( "get_image_bytes", []( Visual& vis ){
    // Inline conversion to python bytes
    const auto cbytes = vis.GetImageBytes();
    std::string sbytes( cbytes.begin(), cbytes.end() );
    return pybind11::bytes( sbytes );
  } )
  .def( "get_image", []( Visual& vis, const bool raw ){
    // Inline conversion of cv::Mat to numpy arrays
    cv::Mat img = vis.GetImage( raw );
    return pybind11::array_t<unsigned char>(
      {img.rows, img.cols, 3},
      img.data );
  } )
  .def_readonly(  "dev_path",     &Visual::dev_path     )
  .def_readwrite( "threshold",    &Visual::threshold    )
  .def_readwrite( "blur_range",   &Visual::blur_range   )
  .def_readwrite( "lumi_cutoff",  &Visual::lumi_cutoff  )
  .def_readwrite( "size_cutoff",  &Visual::size_cutoff  )
  .def_readwrite( "ratio_cutoff", &Visual::ratio_cutoff )
  .def_readwrite( "poly_range",   &Visual::poly_range   )
  ;

  // Required for coordinate calculation
  pybind11::class_<Visual::VisResult>( m, "VisResult" )
  .def_readwrite( "x",         &Visual::VisResult::x            )
  .def_readwrite( "y",         &Visual::VisResult::y            )
  .def_readwrite( "sharpness", &Visual::VisResult::sharpness_m2 )
  .def_readwrite( "s2",        &Visual::VisResult::sharpness_m2 )
  .def_readwrite( "s4",        &Visual::VisResult::sharpness_m4 )
  .def_readwrite( "area",      &Visual::VisResult::area         )
  .def_readwrite( "maxmeas",   &Visual::VisResult::maxmeas      )
  .def_readwrite( "poly_x1",   &Visual::VisResult::poly_x1      )
  .def_readwrite( "poly_x2",   &Visual::VisResult::poly_x2      )
  .def_readwrite( "poly_x3",   &Visual::VisResult::poly_x3      )
  .def_readwrite( "poly_x4",   &Visual::VisResult::poly_x4      )
  .def_readwrite( "poly_y1",   &Visual::VisResult::poly_y1      )
  .def_readwrite( "poly_y2",   &Visual::VisResult::poly_y2      )
  .def_readwrite( "poly_y3",   &Visual::VisResult::poly_y3      )
  .def_readwrite( "poly_y4",   &Visual::VisResult::poly_y4      )
  ;
}
