#!/bin/bash

## Variables for versions
JQUERY_VERSION="3.6.0"
SOCKETIO_VERSION="2.1.1"
PLOTLY_VERSION="1.58.4"
FONTAWESOME_VERSION="5.15.2"

# JQuery host main host site: https://jquery.com/download/
wget https://code.jquery.com/jquery-${JQUERY_VERSION}.min.js \
     --output-document static/external/js/jquery-${JQUERY_VERSION}.min.js

# Socket IO main host site: https://socket.io/docs/v3/client-installation/index.html
# Right now we can only get the non-min version for the older socketio version.
wget https://cdnjs.cloudflare.com/ajax/libs/socket.io/${SOCKETIO_VERSION}/socket.io.js \
     --output-document static/external/js/socket.io-${SOCKETIO_VERSION}.js

# Plotly host site: https://plotly.com/javascript/getting-started/
wget https://cdn.plot.ly/plotly-${PLOTLY_VERSION}.min.js \
     --output-document static/external/js/plotly-${PLOTLY_VERSION}.min.js

# Font awesome host site: https://fontawesome.com/how-to-use/on-the-web/setup/hosting-font-awesome-yourself
wget https://use.fontawesome.com/releases/v${FONTAWESOME_VERSION}/fontawesome-free-${FONTAWESOME_VERSION}-web.zip \
     --output-document static/external/fontawesome-${FONTAWESOME_VERSION}.zip

unzip static/external/fontawesome-${FONTAWESOME_VERSION}-web.zip -d static/external/
