const allow_cookies = Cookies.get("miniconf-allow-cookies-2021");

if (!allow_cookies) {
  $(".gdpr").show();
}

if (allow_cookies) {
  _paq.push(['setConsentGiven']);
  _paq.push(['setCookieConsentGiven']);
}

$(".gdpr-btn").on("click", () => {
  Cookies.set("miniconf-allow-cookies-2021", 1, { expires: 7 });
  $(".gdpr").hide();
});
