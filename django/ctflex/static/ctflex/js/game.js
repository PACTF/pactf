jQuery(document).ready(function () {

    // Hint visibility toggling
    Array.prototype.forEach.call(jQuery(".problem"), function (prob) {
        jQuery(".hint-button", prob).on('click', function (event) {
            jQuery('.hint-content', prob).toggle('show');
        });
    });

});