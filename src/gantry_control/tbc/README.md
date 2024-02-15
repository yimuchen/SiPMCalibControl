# Tileboard controls

Additional methods to help with tileboard control routines. This includes:

- Specialized instances of `zmq_client` to abstract the processes of pulling
  data from the tileboard ELM system. Mainly defined in `tbc.py`

- A better way to format the raw data files into awkward arrays for analysis.
  This is done in 2 parts, the deserialization into a numpy-compatible memory
  map (see `_rocv2.cc`), and additional wrapping to awkward arrays and interaction
  with files (see `rocv2.py`)
