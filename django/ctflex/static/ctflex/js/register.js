jQuery(document).ready(function () {
    initTeamStatus();
    initEligibility();
});

function initEligibility() {
    var country = $('#id_new_team-country');
    var background = $('#id_new_team-background');
    var eligible = $('#eligible-container');

    var syncer = function () {
        syncEligibility(country, background, eligible);
    };

    country.change(syncer);
    background.change(syncer);

    syncer();
}

var eligibility_timeout = -1;

function syncEligibility(country, background, eligible) {
    var ELIGIBLE_GLYPH = 'glyphicon-ok-sign',
        INELIGIBLE_GLYPH = 'glyphicon-info-sign';

    var message = eligible.find('#eligible-message');
    var glyph = eligible.find('#eligible-glyph');

    clearTimeout(eligibility_timeout);

    function setClass(new_text, new_class) {
        glyph.removeClass(INELIGIBLE_GLYPH).removeClass(ELIGIBLE_GLYPH);
        glyph.addClass('glyphicon-refresh').addClass('spinning');
        message.text("Computing eligiblity…")
        eligibility_timeout = setTimeout(function () {
            message.text(new_text);
            glyph.removeClass('glyphicon-refresh').removeClass('spinning');
            glyph.addClass(new_class);
        }, 250);
    }

    if (country[0].value == 'U' && background[0].value == 'S') {
        setClass("Your team is eligible to win prizes!", ELIGIBLE_GLYPH);
    } else {
        setClass("Your team is ineligible to win prizes.", INELIGIBLE_GLYPH);

    }
}

var NEW_TEAM_STATUS = 'new',
    OLD_TEAM_STATUS = 'old';

function initTeamStatus() {
    status_input = jQuery('#team-status');

    jQuery('#new-team-btn').click(function () {
        status_input.val(NEW_TEAM_STATUS);
        syncTeamStatus();
    });

    jQuery('#existing-team-btn').click(function () {
        status_input.val(OLD_TEAM_STATUS);
        syncTeamStatus();
    });

    syncTeamStatus();
}

function syncTeamStatus() {
    var status = jQuery('#team-status').val();
    if (status == NEW_TEAM_STATUS) {
        var show_bit = 'new', hide_bit = 'existing';
    } else if (status == OLD_TEAM_STATUS) {
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
