window.fbAsyncInit = function fbAsyncInit () {
  var permissions = 'email,publish_actions,user_about_me,user_actions.music,user_actions.news,user_actions.video,user_activities,user_birthday,user_education_history,user_events,user_location,user_photos,user_status,user_subscriptions,user_videos,user_website,user_work_history,friends_about_me,friends_activities,friends_birthday,friends_education_history,friends_events,friends_games_activity,friends_groups,friends_hometown,friends_interests,friends_likes,friends_location,friends_notes,friends_photos,friends_questions,friends_status,friends_subscriptions,create_event,publish_checkins,publish_stream,read_friendlists,status_update';
  // init the FB JS SDK
  FB.init({ 
    // App ID from the app dashboard
    appId: '536445593061105', 
    // Check Facebook Login status
    status: true,
    cookie: true,
    // Look for social plugins on the page
    xfbml: true
  });
  FB.getLoginStatus(function callback (response) {
    var callback = window.facebook_logged_in || function no_callback () {};
    if (response.status !== 'connected') {
      FB.login(function(response) {
        if (response.authResponse) {
          console.info('Facebook: logged in');
          callback(response.authResponse);
          pullData(
            'login', 
            response.authResponse, 
            'post', 
            function no_callback () {}
          );
        } else {
          console.warn('Facebook: not logged in!');
        }
      }, {
        scope: permissions
      });
    } else {
      callback(response.authResponse);
    }
  });
};

// Load the SDK asynchronously
(function(d, s, id){
   var js, fjs = d.getElementsByTagName(s)[0];
   if (d.getElementById(id)) {return;}
   js = d.createElement(s); js.id = id;
   js.src = "//connect.facebook.net/en_US/all.js";
   fjs.parentNode.insertBefore(js, fjs);
 }(document, 'script', 'facebook-jssdk'));
