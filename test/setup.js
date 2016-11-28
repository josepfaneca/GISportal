var fs = require('fs');
var path = require('path');
var httpMocks = require('node-mocks-http');
var eventEmitter = require('events').EventEmitter;

var configDestination = path.join(__dirname, '../config/site_settings/127.0.0.1:6789');

before(function() {
   global.mocks = {
      createReq: function() {
         return httpMocks.createRequest({
            headers: {
               host: '127.0.0.1:6789'
            }
         });
      },
      createRes: function() {
         return httpMocks.createResponse({
            eventEmitter: eventEmitter
         });
      }
   };
});

after(function() {
   if (!global.configExists) {
      fs.unlinkSync(configDestination);
   }
});