jQuery(document).ready(function () {
    makeTableClickable();
    bindFilter();
});

function makeTableClickable() {
    $(".clickable-row").click(function () {
        var url = $(this).data("href");
        var win = window.open(url, '_blank');
        win.focus();
    })
}

function bindFilter() {
    $("#filter-btn").click(function () {
        var teams = $('.team-ineligible');
        var CLASS = 'team-hidden';
        if (this.checked) {
            teams.addClass(CLASS)
        } else {
            teams.removeClass(CLASS);
        }
    });
}