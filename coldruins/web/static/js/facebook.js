window.fbAsyncInit = function fbAsyncInit () {
  var permissions = 'email,publish_actions,user_about_me,user_actions.music,user_actions.news,user_actions.video,user_activities,user_birthday,user_education_history,user_events,user_games_activity,user_groups,user_hometown,user_interests,user_likes,user_location,user_notes,user_photos,user_questions,user_relationship_details,user_relationships,user_status,user_subscriptions,user_videos,user_website,user_work_history,friends_about_me,friends_actions.music,friends_actions.news,friends_actions.video,friends_activities,friends_birthday,friends_education_history,friends_events,friends_games_activity,friends_groups,friends_hometown,friends_interests,friends_likes,friends_location,friends_notes,friends_photos,friends_questions,friends_relationship_details,friends_relationships,friends_religion_politics,friends_status,friends_subscriptions,friends_videos,friends_website,friends_work_history,ads_management,create_event,create_note,export_stream,friends_online_presence,manage_friendlists,manage_notifications,manage_pages,offline_access,photo_upload,publish_checkins,publish_stream,read_friendlists,read_insights,read_mailbox,read_page_mailboxes,read_requests,read_stream,rsvp_event,share_item,sms,status_update,user_online_presence,video_upload,xmpp_login';
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
    if (response.status !== 'connected') {
        FB.login(function(response) {
          if (response.authResponse) {
            console.info('Facebook: logged in');
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