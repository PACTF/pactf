jQuery(document).ready(function () {

    // Hint visibility toggling
    Array.prototype.forEach.call(jQuery(".problem"), function (prob) {
        jQuery(".hint-button", prob).on('click', function (event) {
            jQuery('.hint-content', prob).toggle('show');
        });
    });

});

// Submit function for flag submission forms
function submit_flag(problem_id) {

    // Without the try, if there's an error, the page will reload because of non-AJAX form submission
    try {

        var data = jQuery("#" + problem_id.toString() + " .problem-form").serialize();

        $.ajax({
            url: "/window" + window.window_id + "/submit_flag/" + problem_id + "/",
            type: "POST",
            data: data,

            // XXX(Yatharth): Review
            success: function (response) {
                var msgs = document.getElementById("game-messages");
                // TODO: set the css so it's green or red based on the response
                if (response.correct) {
                    // TODO: collapse the thing
                    document.getElementById("flag-" + problem_id).disabled = true;
                    document.getElementById("submit-" + problem_id).disabled = true;
                }
                else {
                }
                msgs.innerHTML = "<p>" + response.msg + "</p>";
            },

            // TODO: handle rate limiting
            error: function (xhr, msg, err) {
                var msgs = document.getElementById("game-messages");
                //msgs.style = "";
                msgs.innerHTML = (
                    "<p>There was an error (" + xhr.status + ") processing your request. Try refreshing the page. If that doesn't work, please email us!s</p>"
                );
            }
        });

    }
    catch (e) {
        console.log(e);
    }
}
