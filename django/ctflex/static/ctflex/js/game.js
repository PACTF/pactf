jQuery(document).ready(function () {

    // Hint visibility toggling
    Array.prototype.forEach.call(jQuery(".problem"), function(prob) {
        jQuery(".hint-button", prob).on('click', function (event) {
            jQuery('.hint-content', prob).toggle('show');
        });
    });

    // Enable AJAX for flag submissions
    Array.prototype.forEach.call(jQuery(".problem"), function(prob) {
      var prob_form = jQuery(".flag-submit", prob);
      // There's definitely a better way to do this
      var window = document.getElementById("window-id").innerHTML;
      prob_form.on('submit', function (event) {
        event.preventDefault();
        submit_flag(window, prob.id, prob_form.serialize());
      });
    });

});

function submit_flag(w_id, p_id, data) {
  //console.log(w_id);
  $.ajax({
    url : "/window" + w_id + "/submit_flag/" + p_id + "/",
    type : "POST",
    data : data,

    success : function(response) {
      var msgs = document.getElementById("game-messages");
      // TODO: set the css so it's green or red based on the response
      if (response.correct) {
        // TODO: collapse the thing
        document.getElementById("flag-" + p_id).disabled = true;
        document.getElementById("submit-" + p_id).disabled = true;
      }
      else {
      }
      msgs.innerHTML = "<p>" + response.msg + "</p>";
    },

    error : function (xhr, msg, err) {
      var msgs = document.getElementById("game-messages");
      //msgs.style = "";
      msgs.innerHTML = (
        "<p>There was an error (" + xhr.status + ") processing your request. Try refreshing the page. If that doesn't work, please email us!s</p>"
      );
    }
  });
}
