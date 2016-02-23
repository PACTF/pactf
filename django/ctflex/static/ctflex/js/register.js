var NEW_TEAM_STATUS = 'new',
    EXISTING_TEAM_STATUS = 'old';

// TODO: Rename all of existing to 'old'

jQuery(document).ready(function () {

    status_input = jQuery('#team-status');

    jQuery('#new-team-btn').click(function () {
        status_input.val(NEW_TEAM_STATUS);
        syncTeamStatus();
    });

    jQuery('#existing-team-btn').click(function () {
        status_input.val(EXISTING_TEAM_STATUS);
        syncTeamStatus();
    });

    syncTeamStatus();
});

function syncTeamStatus() {
    var status = jQuery('#team-status').val();
    if (status == NEW_TEAM_STATUS) {
        var show_bit = 'new', hide_bit = 'existing';
    } else if (status == EXISTING_TEAM_STATUS) {
        var show_bit = 'existing', hide_bit = 'new';
    } else {
        console.log("Did not recognize team status: '" + status + "'");
        return;
    }

    var show_btn = jQuery('#' + show_bit + '-team-btn');
    var hide_btn = jQuery('#' + hide_bit + '-team-btn');
    var hide_container = jQuery('#' + hide_bit + '-team-container');
    var show_container = jQuery('#' + show_bit + '-team-container');
    var common_container = jQuery('#common-team-container');
    var name_input = jQuery('#id_' + show_bit + '_team-name')

    if (show_btn.hasClass('active')) {
        console.log("Button for " + show_bit + "was already active");
        return;
    }

    show_btn.addClass('active');
    hide_btn.removeClass('active');

    hide_container.find('.form-control').prop('disabled', true);
    show_container.find('.form-control').prop('disabled', false);

    common_container.hide('fast');
    hide_container.hide('fast', function () {
        show_container.show('normal');
        common_container.show('normal');
        name_input.focus();
    });
}
