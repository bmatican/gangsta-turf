jQuery(function jquery_dom_loaded () {
  
});

window.facebook_logged_in = function facebook_logged_in (authResponse) {
  FB.api('/me', function facebook_api_callback (response) {
    $('#user').html(response.first_name+' '+response.last_name);
  });
}

var dir = {
  images: '/static/img'
};

var icons = {
  gold: dir.images + '/pin_gold.png',
  beer: dir.images + '/pin_beer.png',
  iron: dir.images + '/pin_iron.png',
  stone: dir.images + '/pin_stone.png',
  wood: dir.images + '/pin_wood.png',
};

var map;

var markers = [];

function initialize() {

// Create an array of styles.
  var styles = [
    {
      stylers: [
        { hue: "#D66300" },
        { saturation: -20 }
      ]
    }
  ];

  // Create a new StyledMapType object, passing it the array of styles,
  // as well as the name to be displayed on the map type control.
  var styledMap = new google.maps.StyledMapType(styles,
    {name: "Styled Map"});

  // Create a map object, and include the MapTypeId to add
  // to the map type control.
  var mapOptions = {
    zoom: 15,
    center: new google.maps.LatLng(51.52038666, -0.15483856),
    mapTypeControlOptions: {
      mapTypeIds: [google.maps.MapTypeId.ROADMAP, 'map_style']
    }
  };
  map = new google.maps.Map(document.getElementById('map-canvas'),
    mapOptions);

  //Associate the styled map with the MapTypeId and set it to display.
  map.mapTypes.set('map_style', styledMap);
  map.setMapTypeId('map_style');

  google.maps.event.addListener(map, "click", function(e){
    add_location_marker('wood beer gold stone iron'.split(' ')[Math.floor(Math.random()*5)], e.latLng);
  });
}

google.maps.event.addDomListener(window, 'load', initialize);

function add_location_marker (type, location) {
  if (!icons[type]) {
    console.warn('[add_location_marker] Unknown type :'+type);
    return null;
  }
  var marker = new google.maps.Marker({
    position: location,
    map: map,
    icon: icons[type]
  });
  markers.push(marker);
  return marker;
}