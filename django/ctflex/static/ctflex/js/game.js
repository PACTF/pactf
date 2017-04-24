jQuery(document).ready(function () {


    Array.prototype.forEach.call(jQuery(".problem"), function (prob) {

        jQuery(".problem-header", prob).on('click', function (event) {
            if (!$(event.target).closest('.header-link').length) {
                jQuery(".problem-body", prob).toggle('show');
            }
        });

        // Hint visibility toggling
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
            url: "/api/submit_flag/" + problem_id + "/",
            type: "POST",
            data: data,

            // XXX(Yatharth): Review
            success: function (response) {
                if (response.status <= 0) {
                    jQuery("#" + problem_id + " .problem-body").toggle('show');
                    jQuery("#" + problem_id + " .problem-header").html(function (index, html) {
                        return html.replace(/Unsolved/, 'Solved');
                    });
                    jQuery("#" + problem_id + " .problem-form").html(function (index, html) {
                        return "<p>Your team has already solved this problem!</p>";
                    })
                }

                if (response.status === 0) {
                    jQuery("#navbar-score").text(function (i, value) {
                        return parseInt(value) + parseInt(jQuery("#" + problem_id + " .problem-points").text());
                    });
                }

                var prefix = response.status === 0 ? "Success! " : response.status === 1 ? "Incorrect! " : "";
                var style = response.status === -1 ? "info" : response.status === 0 ? "success" : "error";
                jQuery.notify(prefix + response.message, style);
            },

            error: function (xhr, msg, err) {
                jQuery.notify("There was an error (" + xhr.status + ") processing your request. Try refreshing the page. If that doesn't work, please email us!", "error");
            }
        });

    }
    catch (e) {
        jQuery.notify("Error contacting the PACTF server. Please wait and try again.", "warn");
        console.debug(e);
    }
}
