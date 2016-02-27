function remainingTime(endtime, max_microseconds) {
    var delta = endtime - Date.parse(new Date());

    if (max_microseconds && delta > max_microseconds) {
        delta = max_microseconds;
    }

    var seconds = Math.floor((delta / 1000) % 60);
    var minutes = Math.floor((delta / 1000 / 60) % 60);
    var hours = Math.floor((delta / (1000 * 60 * 60)) % 24);
    var days = Math.floor(delta / (1000 * 60 * 60 * 24));
    return {
        'total': delta,
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds
    };
}

function initializeCountdown() {
    var endtime = new Date(Date.parse(window.js_context.countdown_endtime));
    var max_microseconds = parseInt(window.js_context.countdown_max_microseconds);

    var clock = jQuery('#timer');
    var daysSpan = jQuery('.days > .value', clock);
    var hoursSpan = jQuery('.hours > .value', clock);
    var minutesSpan = jQuery('.minutes > .value', clock);
    var secondsSpan = jQuery('.seconds > .value', clock);

    function updateClock() {
        var time = remainingTime(endtime, max_microseconds);

        daysSpan.text(time.days);
        hoursSpan.text(time.hours);
        minutesSpan.text(('0' + time.minutes).slice(-2));
        secondsSpan.text(('0' + time.seconds).slice(-2));

        if (time.total <= 0) {
            clearInterval(timeinterval);
            document.location.reload(true);
        }
    }

    updateClock();
    var timeinterval = setInterval(updateClock, 1000);
}

if (document.addEventListener) {
    document.addEventListener('js_context', initializeCountdown, false);
} else {
    document.attachEvent('js_context', initializeCountdown);
}
