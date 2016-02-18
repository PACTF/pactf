function attempt_login() {
  $.ajax({
    url : "/login/",
    type : "POST",
    data : $('#login-attempt').serialize(),

    success : function(response) {
      console.log(response);
    },

    error : function(xhr, msg, err) {
      alert(err);
    }
  });
}
