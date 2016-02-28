jQuery(document).ready(function () {

    // Hint visibility toggling
    Array.prototype.forEach.call(jQuery(".problem"), function (prob) {
        // there is definitely a better way to do this
        if (jQuery(".problem-solved-status", prob).html().includes("Solved")) {
            jQuery(".problem-body", prob).collapse("hide");
        }
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
                var style = "error";
                // XXX(Yatharth): Have a blanket except as "internal server error" and add "could not communicate" error if can't parse on client side
                if (response.status == 0 || response.status == 2) {
                    jQuery("#" + problem_id + "-body").collapse();
                    jQuery("#" + problem_id + " .problem-header").html(function (index, html) {
                        return html.replace(/Unsolved/, 'Solved');
                    });
                    style = "success";
                }
                jQuery.notify(response.message, style);
            },

            // TODO: handle rate limiting
            error: function (xhr, msg, err) {
                jQuery.notify("There was an error (" + xhr.status + ") processing your request. Try refreshing the page. If that doesn't work, please email us!", "error");
            }
        });

    }
    catch (e) {
        jQuery.notify("Error contacting the PACTF server. Please wait and try again.", "warn");
        console.log(e);
    }
}
