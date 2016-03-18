jQuery(document).ready(function () {
    var parser = document.createElement('a');
    parser.href = window.location.href;
    var url = "/api/unread_announcements/"; // + parser.pathname.split('/').slice(-2)[0];

    updateCount(url);

    setInterval(function () {
        updateCount(url)
    }, 1000 * 20);
});

function updateCount(url) {

    // TODO(Cam): Make it a POST request instead of GET
    $.ajax({
        url: url,
        type: "GET",
        data: {},

        success: function (response) {
            var announcebar = jQuery("#unread-announcements-badge");
            if (response.count > 0) {
                if (parseInt(announcebar.html()) < response.count) {
                    jQuery.notify("You have unread announcements.");
                }

                announcebar.html("" + response.count);
                announcebar.css("display", "inline");
            }
            else {
                announcebar.html("0");
                announcebar.css("display", "none");
            }
        },

        error: function (xhr, msg, err) {
            jQuery.notify(
                "Unable to connect to the PACTF server.\n" +
                "This could be our fault. Try waiting a few seconds, or refresh!"
            );
        }
    });
}


(function () {


})();

