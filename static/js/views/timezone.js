const current_timezone = getTimezone();
$(".selectedTimezone").html(moment().tz(current_timezone).format("Z"));

function getTimezone() {
    const url_timezone = window.getUrlParameter && getUrlParameter('tz');
    if (url_timezone) return url_timezone;

    const storage_timezone = window.localStorage.getItem("tz")
    if (storage_timezone) return storage_timezone;

    return moment.tz.guess();
}

// compute relative time
$(document).ready(function () {
    $(".relative-time").each((_, e) => {
        const element = $(e);
        const timestamp = element.text();

        let output = moment(timestamp).fromNow();
        element.text(output);
    });

    $(".current-time").each((_, e) => {
        const element = $(e);

        // update every 30s
        let timer = () => {
            const curTime = moment().tz(current_timezone).format("dddd, MMM Do @ HH:mm");
            element.text(`Your current time: ${curTime}`);
            setTimeout(() => {
                timer();
            }, 30 * 1000);
        };
        timer();
    });
});