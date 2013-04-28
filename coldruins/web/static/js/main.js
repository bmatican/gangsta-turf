jQuery(function jquery_dom_loaded () {
  
});

window.facebook_logged_in = function facebook_logged_in (authResponse) {
  FB.api('/me', function facebook_api_callback (response) {
    $('#user').html(response.first_name+' '+response.last_name);
    $('#user_img').attr('src', response.picture.data.url);
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
        },
        {
          featureType: "transit",
          stylers: [
            { visibility: "off" }
          ]
        },
        {
          featureType: "poi.park",
          elementType: "labels.icon",
          stylers: [
            { color: '#FFECE0' },
            // { hue: "#ff0000" },
            { visibility: "simplified" }
          ]
        },
        {
          featureType: 'poi',
          stylers: [
            { visibility: 'off' }
          ]
        },
        {
          featureType: 'road',
          elementType: 'labels.icon',
          stylers: [
            { visibility: 'off' }
          ]
        },
        {
          featureType: 'road',
          elementType: 'labels.text.stroke',
          stylers: [
            { color: '#a27a54' }
          ]
        },
        {
          featureType: 'road',
          elementType: 'labels.text.fill',
          stylers: [
            { color: '#ffffff' }
          ]
        },
        {
          featureType: 'road',
          elementType: 'geometry.fill',
          stylers: [
            { color: '#a27a54' }
          ]
        },
        {
          featureType: 'road',
          elementType: 'geometry.stroke',
          stylers: [
            { color: '#ffffff' }
          ]
        },
        {
          featureType: 'landscape',
          stylers: [
            { color: '#d1b396' }
          ]
        },
        {
          featureType: 'landscape.natural',
          stylers: [
            { color: '#C7D9C3' }
          ]
        },
        {
          featureType: 'water',
          stylers: [
            { color: '#e2efff'}
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