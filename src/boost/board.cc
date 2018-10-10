#include <board.hpp>
#include <boost/python.hpp>

BOOST_PYTHON_MODULE( board )
{
  boost::python::class_<Board>( "Board" )
  .def( "set_boardtype", &Board::set_boardtype )
  .def( "has_chip",      &Board::has_chip )
  .def( "get_chip_x",    &Board::get_chip_x )
  .def( "get_chip_y",    &Board::get_chip_y )
  .def_readwrite( "boardtype", &Board::boardtype )
  .def_readonly( "chip_pos", &Board::chip_pos )
  .def_readonly( "op_chip",  &Board::op_chip );
}
