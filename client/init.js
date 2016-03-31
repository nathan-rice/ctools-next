require('./css/ctools.css');
rbush = require('rbush');
numeric = require('numeric');


// onGoogleReady is being defined as a global function on purpose
onGoogleReady = function() {
    var mapDiv = document.getElementById('map'),
        mapOptions = {
            zoom: 8,
            center: new google.maps.LatLng(-34.397, 150.644),
            mapTypeId: google.maps.MapTypeId.ROADMAP
        },
        map = new google.maps.Map(mapDiv, mapOptions);
    // the ctools module must be loaded after the Google maps api
    ctools = require('./ctools.js');
};