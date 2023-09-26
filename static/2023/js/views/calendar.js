// yeah, globals are bad but it makes it easy

const dayData = [
  { text: "Sun, Oct 16", day: "Sunday" },
  { text: "Mon, Oct 17", day: "Monday" },
  { text: "Tue, Oct 18", day: "Tuesday" },
  { text: "Wed, Oct 19", day: "Wednesday" },
  { text: "Thu, Oct 20", day: "Thursday" },
  { text: "Fri, Oct 21", day: "Friday" },
];

// names for render modes
const filter_sessions = {
  all: "All sessions",
  bookmarked: "Bookmarked sessions",
}

const current_filter =
  getUrlParameter("filter") || window.localStorage.getItem("filter");
const filterNames = ["All sessions", "Bookmarked sessions"];

function finishCalendar(renderPromises) {
  updateKey();
  updateTzDropdown();
  updateFilterDropdown();

  renderPromises.push(updateFullCalendar());

  // only when everything has rendered do we update times in the calendar
  Promise.all(renderPromises).then(() => {
    updateTimezone();
    tippy("[data-tippy-content]", { trigger: "mouseenter focus" });
  });
}

function getTimezone() {
  const urlTz = window.getUrlParameter && getUrlParameter("tz");
  if (urlTz) return urlTz;

  const storageTz = window.localStorage.getItem("tz");
  if (storageTz) return storageTz;

  return moment.tz.guess();
}

function updateTzDropdown() {
  const current_tz =
    getUrlParameter("tz") ||
    window.localStorage.getItem("tz") ||
    moment.tz.guess();
  const tzNames = [...moment.tz.names()];

  const setupTZSelector = () => {
    const tzOptons = d3.selectAll("select.tzOptions");
    tzOptons
      .selectAll("option")
      .data(tzNames)
      .join("option")
      .attr("data-tokens", (d) => d.split("/").join(" "))
      .attr("selected", (d) => (d === current_tz ? true : null))
      .text((d) => d);

    $(".selectpicker")
      .selectpicker({ liveSearch: true })
      .on("changed.bs.select", function (
        e,
        clickedIndex,
        isSelected,
        previousValue
      ) {
        new_tz = tzNames[clickedIndex];

        const { localStorage } = window;
        localStorage.setItem("tz", new_tz);

        window.open(`${window.location.pathname}?tz=${new_tz}`, "_self");
      });

    $(".saveTz").on("click", function (_) {
      const new_tz = $(".selectpicker").val();

      const { localStorage } = window;
      localStorage.setItem("tz", new_tz);

      window.open(`${window.location.pathname}?tz=${new_tz}`, "_self");
    });

    $(".resetTz").on("click", function (_) {
      const { localStorage } = window;
      localStorage.removeItem("tz");
      window.open(window.location.pathname, "_self");
    });
  };

  setupTZSelector();
}

function updateFilterDropdown() {
  // const current_filter = getUrlParameter('filter') || window.localStorage.getItem("filter");

  const setupFilterSelector = () => {
    const filterOptons = d3.selectAll("div.filterOptions")
    // const filterOptons = d3.selectAll("select.filterOptions");
    const inputFiltersEnter = filterOptons
      .selectAll("input,label")
      .data(filterNames)
      .enter()

    inputFiltersEnter
      .append('label')
      .attr("class", "btn btn-outline-secondary selectpickerFilter")
      .classed("active", (d) => {
        const isCurrentFilter = d === current_filter
        return (isCurrentFilter ? true : null)
      })
      .text((d) => d)
      .insert('input')
      .attr("type","radio")
      // .attr("class","btn-check")
      .attr("name","options")
      .attr("class", "selectpickerFilter")
      .attr("autocomplete","off")
      .attr("id",(d) => d)
      .attr("value",(d) => d)
      .attr("checked", (d) => {
        return (d === current_filter ? true : null)
      })
    ;
    $('input').click( function(e,
                               clickedIndex,
                               isSelected,
                               previousValue){
      const new_filter = e.target.getAttribute('value');
      const { localStorage } = window;
      localStorage.setItem("filter", new_filter);
      // Check if we are in the overview ore
      window.open(
        `${window.location.pathname}?filter=${new_filter}${window.location.hash}`,
        "_self"
      );
    }).button('toggle');
    $(".selectpickerFilter")
      // .selectpickerFilter({ liveSearch: true })
      .on('toggle', function(){
        const new_filter = filterNames[clickedIndex];
      })
    $(".selectpickerFilter")
      // .selectpickerFilter({ liveSearch: true })
      .on("changed.bs.select", function (
        e,
        clickedIndex,
        isSelected,
        previousValue
      ) {
        const new_filter = filterNames[clickedIndex];
        const { localStorage } = window;
        localStorage.setItem("filter", new_filter);
        // Check if we are in the overview ore
        window.open(
          `${window.location.pathname}?filter=${new_filter}${window.location.hash}`,
          "_self"
        );
      });
  };

  setupFilterSelector();
}

function updateKey() {
  // finally, render a color legend
  const itemMapping = {
    vis: "Conference",
    paper: "Papers",
    associated: "Associated Events / Symposium",
    workshop: "Workshop",
    application: "Application Spotlights",
    panel: "Tutorial / Panel / Meetup",
  };

  $.get("serve_config.json").then((config) => {
    // filter to top-level things
    const legendColors = [];
    for (const eventType in itemMapping) {
      const legendColor = {
        key: itemMapping[eventType],
        value: config.calendar.colors[eventType],
      };
      legendColors.push(legendColor);
    }

    const legendItems = d3
      .select("#color-legend")
      .selectAll(".legend-item")
      .data(legendColors)
      .enter()
      .append("div")
      .attr("class", "legend-item px-2 d-flex align-items-baseline")
      .attr("id", (d) => `legend-item-${d.key}`);

    legendItems
      .append("div")
      .style("width", "12px")
      .style("height", "12px")
      .style("background-color", (d) => d.value)
      .style("margin-right", "7px");

    legendItems.append("p").text((d) => d.key);
  });
}

function updateFullCalendar(day) {
  const calendar = d3.select(`#calendar${day != null ? `-${day}` : ""}`);
  const allSessions = calendar
    .selectAll("g.all-sessions")
    .data([1])
    .join("div")
    .attr("class", "all-sessions");
  allSessions.selectAll(".day").remove();

  let calendar_json = "serve_main_calendar.json";

  // are we making the full calendar or an individual day's calendar?
  if (day != null) {
    calendar_json = `serve_calendar_${day}.json`;
    populateTimes(calendar);
  } else {
    populateDays(calendar);
    populateTimes(calendar);
  }
  // return deferred promise
  return $.when($.get("serve_config.json"), $.get(calendar_json)).done(
    (config, events) => {
      Promise.all([getBookmarks(events[0])]).then(() => {
        if (day != null) {
          populateRooms(calendar, config[0].room_names, day);
          createDayCalendar(calendar, config[0], events[0]);
        } else {
          showFilteredSessionList(events[0])
          createFullCalendar(calendar, config[0], events[0]);
        }
      });
    }
  );
}

function addSessionHeader(dayString) {
  if (current_filter === "Bookmarked sessions") {
    d3.selectAll('.sessions-header').insert("h1").text("Bookmarked list of sessions"+dayString)
  } else {
    d3.selectAll('.sessions-header').insert("h1").text("Full list of sessions"+dayString)
  }
}

const showFilteredSessionList = (allEvents) => {
  return Promise.all([
    allEvents,
    API.getPapers(),
    API.markGetAll(API.storeIDs.bookmarked),
  ]).then(([allEvents, papers, bookmarks]) => {
    // Have to first get the current tab since all tabs have the same name

    if(current_filter === filter_sessions.bookmarked) {
      addSessionHeader("")

      const bookmarkedPapers = papers.filter((d) => d.bookmarked);
      const bookmarkedSessions = allEvents.filter((d) => d.bookmarked);
      console.log(bookmarks)
      const contentObj = d3.select(`.content`);
      const sessions2 = d3.select('.content').selectAll("session-group-date-slot.session-listing-row")
      const sessionsData = sessions2.data(allEvents, node => {
        node.id
      });

      const newData = sessionsData
        .join((enter) => {
          const groupEL = enter;
          const group = groupEL.select('.session-listing-bookmark')
          return group;
        })

      for (let ev of allEvents) {
        let el = document.getElementsByClassName("row py-3 session-listing-row "+ev.id)[0];
        let dayMobile = document.getElementsByClassName("container mobile-calendar-container")[0];
        let elMobile = dayMobile.getElementsByClassName("row py-3 session-listing-row "+ev.id)[0];
        let elChild = el.getElementsByClassName('session-listing-bookmark')[0]
        let elChildMobile = elMobile.getElementsByClassName('session-listing-bookmark')[0]
        if (!ev.bookmarked) {
          el.style.display = "none"
          elMobile.style.display = "none"
        } else {
          const currNode = d3.select(elChild)
          currNode.classed("selected", ev.bookmarked)
          const currNodeMobile = d3.select(elChildMobile)
          currNodeMobile.classed("selected", ev.bookmarked)
        }
      }

      const timeslots = contentObj.selectAll(".session-group-date-slot");
      timeslots.each(function(d, i, nodeList) {
        const currentElement = d3.select(nodeList[i]);
        // let el = document.getElementsByClassName("row py-3 session-listing-row "+ev.id)[0];
        let noChild = true;
        currentElement
          .selectAll(".session-listing-row")
          .filter(function() {
            if (this.style.display !== "none") {
              noChild = false;
            }
          });
        if (noChild) {
          currentElement.style("display", "none");
        }
      });

      const timeslots_mobile = contentObj.selectAll(".timeslot-container");
      timeslots_mobile.each(function(d, i, nodeList) {
        const currentElement = d3.select(nodeList[i]);
        // let el = document.getElementsByClassName("row py-3 session-listing-row "+ev.id)[0];
        let noChild = true;
        currentElement
          .selectAll(".session-listing-row")
          .filter(function() {
            if (this.style.display !== "none") {
              noChild = false;
            }
          });
        if (noChild) {
          currentElement.style("display", "none");
        }
      });

    } else {
      for (let ev of allEvents) {
        let el = document.getElementsByClassName("row py-3 session-listing-row "+ev.id)[0];
        let elChild = el.getElementsByClassName('session-listing-bookmark')[0]
        let dayMobile = document.getElementsByClassName("container mobile-calendar-container")[0];
        let elMobile = dayMobile.getElementsByClassName("row py-3 session-listing-row "+ev.id)[0];
        let elChildMobile = elMobile.getElementsByClassName('session-listing-bookmark')[0]
        //bookmarking
        let bookmarkEl = document.getElementsByClassName("session-listing-bookmark "+ev.id+" checkbox-bookmark fas")
        d3.selectAll(bookmarkEl).on("click", function() {
          let selection = d3.select(this)
          const new_value = !selection.classed("selected");
          API.markSet(API.storeIDs.bookmarked, ev.id, new_value).then(selection.classed("selected", new_value));
          let sessionData = allEvents.find(e => e.id === ev.id)
          sessionData.bookmarked = new_value;
          ev.bookmarked = new_value;
          //update slots
          let elSlotMark = document.getElementsByClassName("slotIcon checkbox-bookmark fas "+ev.id)[0];
          let elSlotNumber = document.getElementsByClassName("slotIcon bookmarks filter "+ev.id)[0];
          if(!new_value){
            elSlotMark.style.display = "none"
            elSlotMark.style.display = "none"
          } else {
            elSlotMark.style.display = "block"
            elSlotMark.style.display = "block"
          }
        })
        if (!ev.bookmarked) {
          // el.style.display = "none"
        } else {
          const currNode = d3.select(elChild)
          currNode.classed("selected", ev.bookmarked)
          const currNodeMobile = d3.select(elChildMobile)
          currNodeMobile.classed("selected", ev.bookmarked)
        }
      }
    }
  });
};


const getBookmarks = (allEvents) => {
  return Promise.all([
    API.getPapers(),
    API.markGetAll(API.storeIDs.bookmarked),
  ]).then(([papers, bookmarks]) => {

    // Get all current bookmarks for papers
    // Get session id of paper via session_id
    // Get all current bookmarks on sessions

    // Set all session bookmarks to false in case we removed a bookmark
    allEvents.forEach((session) => {
      session.bookmarked = false;
      session.bookmarks = [];
    });

    // Add bookmarks to sessions whose papers where bookmarked
    let bookmarkedPapers = []
    papers.forEach((paper) => {
      if(Object.keys(bookmarks).includes(paper.UID)) {
        paper.bookmarked = true;
        bookmarkedPapers.push(paper)
      }
    });

    // Add bookmarks to sessions
    allEvents.forEach((session) => {
      if(Object.keys(bookmarks).includes(session.id)) {
        session.bookmarked = true;
      }
    });

    bookmarkedPapers.forEach((paper) => {
      const session = allEvents.filter((d) => d.id === paper.session_id);
      if (session.length > 0) {
        session[0].bookmarked = true;
        session[0].bookmarks.push(paper.UID);
        API.markSet(API.storeIDs.bookmarked, session[0].id, true).then();
      }
    });

    // Filter all events if we have filtering on
    // if(current_filter === "bookmarked sessions"){
    //   allEvents = allEvents.filter(d => d.bookmarked)
    // }

    // For each paper bookmark, check if the session it is in is already bookmarked
    // If not, bookmark the session
  });
};

function createFullCalendar(calendar, config, allEvents, sessionsUpdate) {
  if (current_filter === "Bookmarked sessions") {
    allEvents = allEvents.filter((d) => d.bookmarked);
  }

  // there's a strong assumption here that all parallel sessions are aligned on start/end time
  // It gets around this by forcing the overview calendar to be oversimplified
  const sessions_by_day_and_time = d3.group(
    allEvents,
    (d) => d.start.split("T")[0],
    (d) => {
      if (d.id === "conf6" || d.id == "conf7") {
        return "specialtimeslot";
      }
      return d.start.split("T")[1];
    }
  );

  for (const dayKey of sessions_by_day_and_time.keys()) {
    const dayEvents = sessions_by_day_and_time.get(dayKey);

    for (const timeslotKey of dayEvents.keys()) {
      // fill in positioning based on first session (should be grouped already)
      const sessions = dayEvents.get(timeslotKey);
      const dayPosition = `${sessions[0].day} / auto`;
      let timePosition = `${sessions[0].timeStart} / ${sessions[0].timeEnd}`;

      // manually skip adding these groups to clean up Sunday/Monday
      if (dayKey === "2023-10-16" || dayKey === "2023-10-17") {
        if (!(timeslotKey === "14:00:00Z" || timeslotKey === "19:00:00Z")) {
          continue;
        }

        if (timeslotKey === "14:00:00Z") {
          // Force session to end for lunch on overview calendar
          timePosition = `${sessions[0].timeStart} / ` + `time-1200`;
        }

        if (timeslotKey === "14:00:00Z") {
          // Force session to end for lunch on overview calendar
          timePosition = `${sessions[0].timeStart} / ` + `time-1200`;
        }

        // Force VDS to end on time argh
        // // ignore vizsec-2 (starts at 10:05)
        // if (dayKey === "2021-10-27" && timeslotKey === "15:05:00Z")
        //   continue;
        // console.log("dayKey is ", dayKey, " and timeslotKey is ", timeslotKey)
        // if (dayKey === "2023-10-16" && timeslotKey === "14:00:00Z") {
        //   // Force session to end for lunch on overview calendar
        //   timePosition = sessions[0].timeStart + " / " + "time-1015";
        // }

        // force non-full day event on Monday
        // if (dayKey === "2021-10-25" && timeslotKey === "13:00:00Z")
        //   timePosition = sessions[1].timeStart + " / " + sessions[1].timeEnd;
        // if (dayKey === "2021-10-25" && timeslotKey === "17:00:00Z")
        //   timePosition = sessions[3].timeStart + " / " + sessions[3].timeEnd;
      }
      // if (dayKey === "2021-10-26" || dayKey === "2021-10-27") {
      //   if (timeslotKey === "20:00:00Z")
      //     continue;
      // }
      // // ignore vizsec-2 (starts at 10:05)
      // if (dayKey === "2021-10-27" && timeslotKey === "15:05:00Z")
      //   continue;

      const navigateToDay = (_ev, d) => {
        const day_num = d.day.split("-")[1];
        const day_name = dayData[day_num - 1].day;
        $(`.nav-pills a[href="#tab-${day_name}"]`).tab("show");
      };

      const timeslot = calendar
        .append("div")
        .style("grid-column", dayPosition)
        .style("grid-row", timePosition)
        .classed("session-group", sessions.length !== 1)
        .on("click", (ev) => navigateToDay(ev, sessions[0]))
        .on("keydown", (ev) => {
          if (ev.key === " " || ev.key === "Enter")
            navigateToDay(ev, sessions[0]);
        });

      if (sessions.length === 1) {
        const session = sessions[0];
        const slot = timeslot
          .attr("class", "session slot")
          .attr("id", session.id)
          .style("background-color", getColor(session, config))
          .style(
            "color",
            getTextColorByBackgroundColor(getColor(session, config))
          )
          .style("position", "relative")
          .style("padding", "0 10 10 10")
          .text(session.title);

        slot
          .append("div")
          .attr("class", "slotIcon checkbox-bookmark fas "+session.id)
          .classed("invisible", !session.bookmarked)
          .style("display", "block")
          .style("position", "absolute")
          .style("top", "-10px")
          .style("right", "10px")
          .html("&#xf02e;");

        slot
          .append("div")
          .attr("class", "slotIcon bookmarks filter "+session.id)
          .classed("invisible", !session.bookmarked)
          .style("display", "block")
          .style("position", "absolute")
          .style("top", "-2px")
          .style("right", "15px")
          .style("color", "black")
          .text(session.bookmarks.length);
      } else {
        timeslot
          .selectAll(".session")
          .data(sessions, (d) => d.id)
          .join("div")
          .attr("class", "session")
          .style("background-color", (d) => getColor(d, config))
          .style("color", (d) =>
            getTextColorByBackgroundColor(getColor(d, config))
          );
      }
    }
  }
}

function getDayGridRow(timeStart, timeEnd) {
  // Stop weird times from breaking the calendar
  if (timeEnd === "time-1025") {
    timeEnd = "time-1015";
  }

  if (timeStart === "time-1055") {
    timeStart = "time-1045";
  }
  const dayGridRowString = `${timeStart} / ${timeEnd}`;
  return dayGridRowString;
}

function createDayCalendar(calendar, config, dayEvents) {
  if (current_filter === "Bookmarked sessions") {
    dayEvents = dayEvents.filter((d) => d.bookmarked);
  }
  const navigateToSession = (_ev, d) => {
    window.open(d.link, "_blank");
  };

  const sessions = calendar
    .selectAll(".session")
    .data(dayEvents)
    .join("div")
    .attr("class", "session")
    .attr("data-tippy-content", (d) => d.title)
    .style("grid-column", (d) => `${d.room}-start / auto`)
    .style("grid-row", (d) => getDayGridRow(d.timeStart, d.timeEnd))
    .style("background-color", (d) => getColor(d, config))
    .style("color", (d) => getTextColorByBackgroundColor(getColor(d, config)))
    .style("position", "relative")
    .on("click", navigateToSession)
    .on("keydown", (ev, d) => {
      if (ev.key === " " || ev.key === "Enter") navigateToSession(ev, d);
    })
    .text((d) => d.title);
  sessions
    .append("div")
    .attr("class", d => "slotIcon checkbox-bookmark fas "+ d.id)
    .classed("invisible", (d) => !d.bookmarked)
    .style("display", "block")
    .style("position", "absolute")
    .style("top", "-10px")
    .style("right", "10px")
    .html("&#xf02e;");
  sessions
    .append("div")
    .attr("class",  d => "slotIcon bookmarks filter "+ d.id)
    .classed("invisible", (d) => !d.bookmarked)
    .style("display", "block")
    .style("position", "absolute")
    .style("top", "-2px")
    .style("right", "15px")
    .style("color", "black")
    .text((d) => d.bookmarks.length);

}

function populateDays(calendarSelection) {
  // NOTE: `dayData` is defined globally at top of file
  calendarSelection
    .selectAll(".day-slot")
    .data(dayData, (d) => d)
    .join("div")
    .attr("class", "day-slot")
    .style("grid-row", "tracks / auto")
    .style("grid-column", (_d, i) => `day-${i + 1} / auto`)
    .append("h2")
    .append("a")
    .on("click", (ev, d) => {
      $(`.nav-pills a[href="#tab-${d.day}"]`).tab("show");
    })
    .text((d) => d.text);
}

function populateRooms(calendarSelection, roomNames, day) {
  // TODO: use room names
  const roomData = [
    { roomId: "ok1", text: roomNames.ok1, link: "room_ok1.html" },
    { roomId: "ok4", text: roomNames.ok4, link: "room_ok4.html" },
    { roomId: "ok5", text: roomNames.ok5, link: "room_ok5.html" },
    { roomId: "ok6", text: roomNames.ok6, link: "room_ok6.html" },
    { roomId: "ok7", text: roomNames.ok7, link: "room_ok7.html" },
    { roomId: "ok8", text: roomNames.ok8, link: "room_ok8.html" },
    {
      roomId: "mistletoe",
      text: roomNames.mistletoe,
      link: "room_mistletoe.html",
    },
    { roomId: "pinon", text: roomNames.pinon, link: "room_pinon.html" },
  ];

  // truncate rooms added per-day (don't add unnecessary rooms we're not using)
  // switch (day) {
  //   case "Tuesday":
  //     roomData = roomData.slice(0, 2);
  //     break;
  //   case "Friday":
  //     roomData = roomData.slice(0, 7);
  //     break;
  // }

  populateHeader(calendarSelection, roomData);
}

function populateHeader(calendarSelection, data, isDay) {
  // Here's the problem - it's assuming the rooms are named "room1".  See the indexing here.
  const columnPosition = function (d, i) {
    if (isDay) {
      return `day-${i + 1} / auto`;
    }
    return `${d.roomId} / auto`;
  };

  calendarSelection
    .selectAll(".day-slot")
    .data(data, (d) => d)
    .join("div")
    .attr("class", "day-slot")
    .style("grid-row", "tracks / auto")
    .style("grid-column", columnPosition)
    .append("h2")
    .append("a")
    .attr("href", (d) => d.link)
    .text((d) => d.text);
}

function populateTimes(calendarSelection) {
  const timeData = [
    ["8:30 AM CDT", "time-0830"],
    ["9:00 AM CDT", "time-0900"],
    // ["9:30 AM CDT", "time-0930"],
    ["10:15 AM CDT", "time-1015"],
    ["10:45 AM CDT", "time-1045"],
    // ["11:30 AM CDT", "time-1130"],
    ["12:00 PM CDT", "time-1200"],
    // ["1:30 PM CDT", "time-1330"],
    ["2:00 PM CDT", "time-1400"],
    ["3:15 PM CDT", "time-1515"],
    ["3:45 PM CDT", "time-1545"],
    ["5:00 PM CDT", "time-1700"],
  ];

  calendarSelection
    .selectAll(".time-slot:not(.converted-timezone)")
    .data(timeData, (d) => d[0])
    .join("h2")
    .attr("class", "time-slot")
    .attr("data-time", (d) => d[1])
    .style("grid-row", (d) => d[1])
    .text((d) => d[0]);

  calendarSelection
    .selectAll(".converted-timezone")
    .data(timeData, (d) => d[0])
    .join("h2")
    .attr("class", "time-slot converted-timezone")
    .attr("data-time", (d) => d[1])
    .style("grid-row", (d) => d[1])
    .text((d) => d[0]);
}

function resetCalendar() {
  d3.selectAll(".session-group").remove();
  d3.selectAll(".session").remove();
}

function updateTimezone() {
  // get timezone
  const timezone = getTimezone();

  // apply timezone
  $(".converted-timezone").each((_, e) => {
    const element = $(e);
    const hourminutes = element.attr("data-time").split("-")[1];

    const time = moment(
      `2023-10-16 ${hourminutes.slice(0, 2)}:${hourminutes.slice(2, 4)} -05:00`,
      "YYYY-MM-DD HH:mm ZZ"
    );

    const converted_date = time.clone().tz(timezone);
    let converted_time = converted_date.format("HH:mm");

    if (converted_date.format("DD") != time.format("DD"))
      converted_time += "<br>+1 day";

    element.html(converted_time);
  });
}

function getTextColorByBackgroundColor(hexColor) {
  hexColor = hexColor.replace("#", "");
  const r = parseInt(hexColor.substr(0, 2), 16);
  const g = parseInt(hexColor.substr(2, 2), 16);
  const b = parseInt(hexColor.substr(4, 2), 16);
  const yiq = (r * 299 + g * 587 + b * 114) / 1000;
  return yiq >= 128 ? "#000000" : "#ffffff";
}

function getColor(d, config) {
  const color = config.calendar.colors[(d && d.eventType) || "---"];
  return color;
}
