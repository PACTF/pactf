jQuery(document).ready(function () {
   makeTableClickable(); 
});

function makeTableClickable() {
    $(".clickable-row").click(function() {
        window.document.location = $(this).data("href");
    })
}