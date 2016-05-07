jQuery(document).ready(function () {
    makeTableClickable();
});

function makeTableClickable() {
    $(".clickable-row").click(function () {
        var url = $(this).data("href");
        var win = window.open(url, '_blank');
        win.focus();
    })
}
