jQuery(function jquery_dom_loaded () {
  
});

window.facebook_logged_in = function facebook_logged_in (authResponse) {
  FB.api('/me?fields=id,first_name,last_name,picture', function facebook_api_callback (response) {
    $('#user').html(response.first_name+' '+response.last_name);
    $('#user_img').attr('src', response.picture.data.url);
  });
}

var dir = {
  images: '/static/img'
};

var icons = {
  gold: dir.images + '/pin_enemy_gold.png',
  food: dir.images + '/pin_enemy_beer.png',
  iron: dir.images + '/pin_enemy_iron.png',
  stone: dir.images + '/pin_enemy_stone.png',
  wood: dir.images + '/pin_enemy_wood.png',
  gold_own: dir.images + '/pin_own_gold.png',
  food_own: dir.images + '/pin_own_beer.png',
  iron_own: dir.images + '/pin_own_iron.png',
  ston_owne: dir.images + '/pin_own_stone.png',
  wood_own: dir.images + '/pin_own_wood.png',
  gold_clan: dir.images + '/pin_gold.png',
  food_clan: dir.images + '/pin_beer.png',
  iron_clan: dir.images + '/pin_iron.png',
  stone_clan: dir.images + '/pin_stone.png',
  wood_clan: dir.images + '/pin_wood.png',
};

var map;

var markers = [];

var CATEGORIES = [undefined, 'Food & Drinks', 'Arts & Entertainment', 'Shopping & Retail', 'Companies & Education', 'Attractions'];
var CATEGORIES_MAP = [undefined, 'food', 'gold', 'wood', 'iron', 'stone'];

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

  var center = new google.maps.LatLng(51.52038666, -0.15483856);
  if (navigator && navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function get_position (position) {
      center = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
      map.panTo(center);
      pullData(
        'near_location', 
        {center:print_latLong(center), 'distance': 200},
        'post', 
        function (response) {
          var marker = new google.maps.Marker({
            position: center,
            map: map,
            zIndex: 9999
          });
          var places = JSON.parse(response.message);
          for (var i=0; i<places.length; ++i) {
            var type = CATEGORIES_MAP[places[i].fields.category];
            if (places[i].fields.owner != null) {
              console.log(places[i].fields);
              if (places[i].fields.owner == window.userid) {
                type += "_own";
              } else if (true /*TODO: check for clan */) {
                type += "_clan"; 
              }
            }
            add_location_marker(
              places[i].fields.fb_id,
              type,
              new google.maps.LatLng(places[i].fields.lat, places[i].fields.lon)
            );
          };
        }
      );
    });
  }

  // Create a map object, and include the MapTypeId to add
  // to the map type control.
  var mapOptions = {
    zoom: 15,
    center: center,
    mapTypeControlOptions: {
      mapTypeIds: [google.maps.MapTypeId.ROADMAP, 'map_style']
    }
  };
  map = new google.maps.Map(document.getElementById('map-canvas'),
    mapOptions);

  //Associate the styled map with the MapTypeId and set it to display.
  map.mapTypes.set('map_style', styledMap);
  map.setMapTypeId('map_style');
}

google.maps.event.addDomListener(window, 'load', initialize);

function print_latLong (position) {
  return position.toString().slice(1).slice(0,-1).replace(/\s/g, '');
}

function checkin(m) {
  pullData('checkin', {location_id: m.locationid}, 'post', function(rsp) {
    console.log(rsp);
  });
}

function add_location_marker (id, type, location) {
  if (!icons[type]) {
    console.warn('[add_location_marker] Unknown type :'+type);
    return null;
  }
  var marker = new google.maps.Marker({
    position: location,
    map: map,
    icon: icons[type]
  });
  marker.locationid = id;
  markers.push(marker);
  google.maps.event.addListener(marker, 'click', function(e) {
    checkin(marker);
  });
  return marker;
}
