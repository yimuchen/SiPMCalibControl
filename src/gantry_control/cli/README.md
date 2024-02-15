# Programmable control interface

To allow for arbitrary flexibility while still maintaining high reusable code,
the functions in this module mix objects-style with dependency-injection-style
methods. A general rule-of-thumbs for this module would be:

- Object methods should only accept primitive (python-inbuilt) types as inputs
- If 2 non-primitive objects are required for a method, to avoid ambiguity when
  determining either A.method(B) or B.method(A), the modules will keep to using
  `method(A, B)` DI-style methods.
- If more than 2 non-primitive objects are potentially required for a method to
  function. The method should attempt to use the `Session` container as an
  input. The `Session` container (defined in `session.py`) is a generic object
  container that can contain arbitrary types. The initialization of such objects
  stored in the `Session` instance of interest are also defined in the
  `session.py` file.

All other options should be handled by the various functions.
