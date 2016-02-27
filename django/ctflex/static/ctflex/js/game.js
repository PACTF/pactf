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
            url: "/submit_flag/" + problem_id + "/",
            type: "POST",
            data: data,

            // XXX(Yatharth): Review
            success: function (response) {
                // TODO: set the css so it's green or red based on the response
                // XXX(Yatharth): Have a blanket except as "internal server error" and add "could not communicate" error if can't parse on client side
                if (response.status == 0 || response.status == 2) {
                    jQuery("#" + problem_id + " .problem-header").html(function (index, html) {
                        return html.replace(/Unsolved/, 'Solved');
                    });
                    jQuery("#" + problem_id + " .problem-body").remove();
                }
                alert(response.message);
            },

            // TODO: handle rate limiting
            error: function (xhr, msg, err) {
                alert("There was an error (" + xhr.status + ") processing your request. Try refreshing the page. If that doesn't work, please email us!");
            }
        });

    }
    catch (e) {
        console.log(e);
    }
}
