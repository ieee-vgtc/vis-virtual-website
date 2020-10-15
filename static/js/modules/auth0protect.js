window.onload = async () => {
  document.body.style.display = "none";
  $(".secret").hide();
  const auth0 = await createAuth0Client({
    domain: auth0_domain,
    client_id: auth0_client_id,
    cacheLocation: "localstorage",
  });

  const isAuthenticated = await auth0.isAuthenticated();
  const query = window.location.search;

  const updateUI = async () => {
    const is_auth = await auth0.isAuthenticated();
    if (is_auth) {
      document.body.style.display = null;
      const user = await auth0.getUser();
      $(".loginBtn").hide();
      $(".logoutBtn").show();
      $(".secret").show();
      $(".user_name").text(user.name);
    } else {
      $(".loginBtn").show();
      $(".logoutBtn").hide();
      $(".secret").hide();
      $(".user_name").text("");
    }
  };

  if (isAuthenticated) {
    document.body.style.display = null;
    await updateUI();
  } else if (query.includes("code=") && query.includes("state=")) {
    // NEW - check for the code and state parameters
    // Process the login state
    auth0
      .handleRedirectCallback()
      .then((cb) => {
        // console.log(cb, "--- cb");
        window.history.replaceState({}, document.title, "/");
        updateUI();
      })
      .catch((e) => {
        // eslint-disable-next-line no-console
        console.log(e, "--- error");
      });

    // Use replaceState to redirect the user away and remove the querystring parameters
  } else if (
    window.location.href.includes("index.html") &&
    !window.location.hash.includes("index.html")
  ) {
    // await updateUI();
    document.body.style.display = null;
    // const els = document.getElementsByClassName("loginBtn");
    //
    // [].forEach.call(els, function (el) {
    //   el.addEventListener("click", async () => {
    //     await auth0.loginWithRedirect({
    //       redirect_uri: window.location.href,
    //     });
    //   });
    // });
  } else {
    window.location.href = "index.html";
  }

  $(".loginBtn").click(async function () {
    await auth0.loginWithRedirect({
      redirect_uri: window.location.href,
    });
  });
  $(".logoutBtn").click(async function () {
    await auth0.logout({
      redirect_uri: window.location.href,
    });
  });
};
