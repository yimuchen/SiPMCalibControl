# The GUI Client session

The client side uses socket IO to real-time update a web-page to reflect the
status and results of the existing calibration session. Here are try to keep all
the data as simple JavaScript maps to reduce the complexity required for both
server and client, as JSON parser are the only message parsers needed. This
package uses [JQuery](jquery) for element selection and animation, and
[Plotly](plotly) for plotting data.

- [main.js](js/main.js) is the exhaustive list of all interactions within the
  document, including which function handing element interactions, and how to
  process server messages.
- [action.js](js/action.js) is for emission of actions based on the value of
  HTML elements.
- [monitor.js](js/monitor.js) is for processes in the server messages that
  contain data into HTML element updates.
- [monitor_style.js](js/monitor_style.js) are simple few-logic functions that
  handle the styling of the elements generated and altered in the `monitor.js`
  file.
- [input_sync.js](js/input_sync.js) are other server side computation required
  for various eye-candy, such animation and value syncing of text and slider
  elements.

[jquery]: https://jquery.com/
[plotly]: https://plotly.com/javascript/