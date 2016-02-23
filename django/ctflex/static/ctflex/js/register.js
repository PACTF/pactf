jQuery(document).ready(function () {

    jQuery('#new-team-btn').click(function () {
        if (jQuery('#new-team-btn').hasClass('active')) {
            return;
        }

        jQuery(this).addClass('active');
        jQuery('#existing-team-btn').removeClass('active');

        jQuery('#common-team-container').hide('fast');
        jQuery('#existing-team-container').hide('fast', function () {
            jQuery('#new-team-container').show('normal');
            jQuery('#common-team-container').show('normal');
            jQuery('#id_new_team-name').focus();
        });

    });

    jQuery('#existing-team-btn').click(function () {
        if (jQuery('#existing-team-btn').hasClass('active')) {
            return;
        }

        jQuery(this).addClass('active');
        jQuery('#new-team-btn').removeClass('active');

        jQuery('#common-team-container').hide('fast');
        jQuery('#new-team-container').hide('fast', function () {
            jQuery('#existing-team-container').show('normal');
            jQuery('#common-team-container').show('normal');
            jQuery('#id_existing_team-name').focus();
        });


    });

});
