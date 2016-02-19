function attempt_register() {
  $.ajax({
    url : "/register_user/",
    type : "POST",
    data : $('#register-submit').serialize(),

    success : function(response) {
      if ('errors' in response) {
        var err_html = "<p>There were one or more errors:</p>";
        for (var i = 0 ; i < response.errors.length ; i += 1) {
          var err = response.errors[i];
          err_html += "<p>\t" + err[0] + ": " + err[1] + "</p>";
        }
        document.getElementById("errors").innerHTML = err_html;
      }
      else { window.location = response.redirect; }
    },

    error : function(xhr, msg, err) {
      document.getElementById("errors").innerHTML = (
        "<p>There was an error (" + xhr.status + ") processing your request. Try refreshing the page. If that doesn't work, please email us!s</p>"
      );
    }
  });
}
