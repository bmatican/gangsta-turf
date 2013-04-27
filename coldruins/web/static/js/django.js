function getCookie(name) {
  var cookieValue = null, cookies, cookie, i;
  if (document.cookie && document.cookie !== '') {
    cookies = document.cookie.split(';');
    for (i = 0; i < cookies.length; i += 1) {
      cookie = jQuery.trim(cookies[i]);
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
var csrfToken = getCookie('csrftoken');

function csrfSafeMethod(method) {
  // these HTTP methods do not require CSRF protection
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function sameOrigin(url) {
  // test that a given url is a same-origin URL
  // url could be relative or scheme relative or absolute
  var host = document.location.host, // host + port
    protocol = document.location.protocol,
    sr_origin = '//' + host,
    origin = protocol + sr_origin;
  // Allow absolute or scheme relative URLs to same origin
  return (url === origin || url.slice(0, origin.length + 1) === origin + '/') ||
    (url === sr_origin || url.slice(0, sr_origin.length + 1) === sr_origin + '/') ||
    // or any other URL that isn't scheme relative or absolute i.e relative.
    !(/^(\/\/|http:|https:).*/.test(url));
}

$.ajaxSetup({
  beforeSend: function (xhr, settings) {
    if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
      // Send the token to same-origin, relative URLs only.
      // Send the token only if the method warrants CSRF protection
      // Using the CSRFToken value acquired earlier
      xhr.setRequestHeader("X-CSRFToken", csrfToken);
    }
  }
});

function pullData(provider, payload, type, callback) {
  var request = $.ajax({
    url: "/data_provider/" + provider,
    type: type,
    data: {
      "csrfmiddlewaretoken": csrfToken,
      "payload": JSON.stringify(payload)
    }
  });

  request.done(function (response, textStatus, jqXHR) {
    callback(JSON.parse(response));
  });
}
 
