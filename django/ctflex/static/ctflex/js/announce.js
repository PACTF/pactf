setInterval(function() {
  $.ajax({
    url: "/check_news/",
    type: "GET",
    data: {},

    success: function(response) {
      var announcebar = jQuery("#unread-news-badge");
      if (response.num_unread > 0) {
        announcebar.html("" + response.num_unread);
        announcebar.css("display", "inline");
        jQuery.notify("You have unread announcements.");
      }
      else {
        announcebar.html("");
        announcebar.css("display", "none");
      }
    },

    error: function(xhr, msg, err) {
      jQuery.notify(
        "Unable to connect to the PACTF server.\n" +
        "This could be our fault. Try waiting a few seconds, or refresh!"
      );
    }
  });
}, 1000 * 10);
