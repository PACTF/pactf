jQuery(document).ready(function () {

    jQuery('#new-team-btn').click(function () {
        jQuery('#common-team-container').hide('fast');
        jQuery('#existing-team-container').hide('fast', function () {
            jQuery('#new-team-container').show('normal');
            jQuery('#common-team-container').show('normal');
        });
    });

    jQuery('#existing-team-btn').click(function () {
        jQuery('#common-team-container').hide('fast');
        jQuery('#new-team-container').hide('fast', function () {
            jQuery('#existing-team-container').show('normal');
            jQuery('#common-team-container').show('normal');
        });
    });

});
