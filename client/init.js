// onGoogleReady is being defined as a global function on purpose
onGoogleReady = function() {
    var mapDiv = document.getElementById('map'),
        mapOptions = {
            zoom: 8,
            center: new google.maps.LatLng(-34.397, 150.644),
            mapTypeId: google.maps.MapTypeId.ROADMAP
        },
        map = new google.maps.Map(mapDiv, mapOptions);
    // ctools is also being defined as a global variable on purpose
    ctools = require('./ctools.js');
};