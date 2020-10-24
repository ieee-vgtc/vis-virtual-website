const current_timezone = getTimezone();
$(".selectedTimezone").html(moment().tz(current_timezone).format("Z"));

function getTimezone() {
    const url_timezone = window.getUrlParameter && getUrlParameter('tz');
    if (url_timezone) return url_timezone;

    const storage_timezone = window.localStorage.getItem("tz")
    if (storage_timezone) return storage_timezone;

    return moment.tz.guess();
}
