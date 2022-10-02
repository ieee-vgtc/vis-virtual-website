// yeah, globals are bad but it makes it easy

let dayData = [
  { text: "Sun, Oct 16", day: "Sunday" },
  { text: "Mon, Oct 17", day: "Monday" },
  { text: "Tue, Oct 18", day: "Tuesday" },
  { text: "Wed, Oct 19", day: "Wednesday" },
  { text: "Thu, Oct 20", day: "Thursday" },
  { text: "Fri, Oct 21", day: "Friday" },
];

function finishCalendar(renderPromises) {
  updateKey();
  updateTzDropdown();

  renderPromises.push(updateFullCalendar());

  // only when everything has rendered do we update times in the calendar
  Promise.all(renderPromises).then(() => {
    updateTimezone();
    tippy("[data-tippy-content]", {trigger: "mouseenter focus"});
  });
}

function getTimezone() {
  const urlTz = window.getUrlParameter && getUrlParameter('tz');
  if (urlTz) return urlTz;

  const storageTz = window.localStorage.getItem("tz")
  if (storageTz) return storageTz;

  return moment.tz.guess();
}

function updateTzDropdown() {
  const current_tz = getUrlParameter('tz') || window.localStorage.getItem("tz") || moment.tz.guess();
  const tzNames = [...moment.tz.names()];

  const setupTZSelector = () => {
    const tzOptons = d3.selectAll('select.tzOptions')
    tzOptons.selectAll('option').data(tzNames)
      .join('option')
      .attr('data-tokens', d => d.split("/").join(" "))
      .attr('selected', d => d === current_tz ? true : null)
      .text(d => d);

    $('.selectpicker')
      .selectpicker({ liveSearch: true })
      .on('changed.bs.select',
        function (e, clickedIndex, isSelected, previousValue) {
          new_tz = tzNames[clickedIndex];

          const localStorage = window.localStorage;
          localStorage.setItem("tz", new_tz);

          window.open(window.location.pathname + '?tz=' + new_tz, '_self');
        });

    $(".saveTz").on('click', function (_) {
      const new_tz = $(".selectpicker").val();

      const localStorage = window.localStorage;
      localStorage.setItem("tz", new_tz);

      window.open(window.location.pathname + '?tz=' + new_tz, '_self');
    });

    $(".resetTz").on('click', function (_) {
      const localStorage = window.localStorage;
      localStorage.removeItem("tz");
      window.open(window.location.pathname, '_self');
    });
  }

  setupTZSelector();
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

  $.get('serve_config.json').then(config => {
    // filter to top-level things
    let legendColors = [];
    for (const eventType in itemMapping) {
      const legendColor = {
        key: itemMapping[eventType],
        value: config.calendar.colors[eventType],
      }
      legendColors.push(legendColor);
    }

    const legendItems = d3.select('#color-legend').selectAll('.legend-item')
      .data(legendColors)
      .enter().append('div')
      .attr('class', 'legend-item px-2 d-flex align-items-baseline')
      .attr('id', d => 'legend-item-' + d.key);

    legendItems.append('div')
      .style('width', '12px')
      .style('height', '12px')
      .style('background-color', d => d.value)
      .style('margin-right', '7px');

    legendItems.append('p')
      .text(d => d.key);
  });
}

function updateFullCalendar(day) {
  let calendar = d3.select(`#calendar${day != null ? "-" + day : ""}`);
  let allSessions = calendar.selectAll('g.all-sessions')
    .data([1])
    .join('div')
      .attr('class', 'all-sessions');
  allSessions.selectAll('.day').remove();

  let calendar_json = "serve_main_calendar.json";

  // are we making the full calendar or an individual day's calendar?
  if (day != null) {
    calendar_json = `serve_calendar_${day}.json`;
    populateTimes(calendar);
  }
  else {
    populateDays(calendar);
    populateTimes(calendar);
  }

  // return deferred promise
  return $.when($.get('serve_config.json'), $.get(calendar_json))
    .done((config, events) => {
      if (day != null) {
        populateRooms(calendar, config[0].room_names, day);
        createDayCalendar(calendar, config[0], events[0]);
      } else
        createFullCalendar(calendar, config[0], events[0]);
    }
  );
}

function createFullCalendar(calendar, config, allEvents) {
  // there's a strong assumption here that all parallel sessions are aligned on start/end time
  let sessions_by_day_and_time = d3.group(
    allEvents,
    d => d.start.split("T")[0],
    d => d.start.split("T")[1],
  );

  for (const dayKey of sessions_by_day_and_time.keys()) {
    const dayEvents = sessions_by_day_and_time.get(dayKey);

    for (const timeslotKey of dayEvents.keys()) {
      // fill in positioning based on first session (should be grouped already)
      const sessions = dayEvents.get(timeslotKey);
      const dayPosition = sessions[0].day + " / auto";
      let timePosition = sessions[0].timeStart + " / " + sessions[0].timeEnd;

      // manually skip adding these groups to clean up Sunday/Monday
      // if (dayKey === "2021-10-22" || dayKey === "2021-10-23" || dayKey === "2021-10-24" || dayKey === "2021-10-25") {
      //   if (!(timeslotKey === "13:00:00Z" || timeslotKey === "17:00:00Z")) {
      //     continue;
      //   }

      //   // force non-full day event on Monday
      //   if (dayKey === "2021-10-25" && timeslotKey === "13:00:00Z")
      //     timePosition = sessions[1].timeStart + " / " + sessions[1].timeEnd;
      //   if (dayKey === "2021-10-25" && timeslotKey === "17:00:00Z")
      //     timePosition = sessions[3].timeStart + " / " + sessions[3].timeEnd;
      // }
      // if (dayKey === "2021-10-26" || dayKey === "2021-10-27") {
      //   if (timeslotKey === "20:00:00Z")
      //     continue;
      // }
      // // ignore vizsec-2 (starts at 10:05)
      // if (dayKey === "2021-10-27" && timeslotKey === "15:05:00Z")
      //   continue;

      const navigateToDay = (_ev, d) => {
        const day_num = d.day.split('-')[1];
        const day_name = dayData[day_num - 1].day;
        $(`.nav-pills a[href="#tab-${day_name}"]`).tab('show')
      };

      const timeslot = calendar.append('div')
        .style('grid-column', dayPosition)
        .style('grid-row', timePosition)
        .classed('session-group', sessions.length !== 1)
        .on('click', ev => navigateToDay(ev, sessions[0]))
        .on('keydown', (ev) => {
          if (ev.key === " " || ev.key === "Enter")
            navigateToDay(ev, sessions[0]);
        });

      if (sessions.length === 1) {
        const session = sessions[0];
        timeslot.attr('class', 'session')
          .attr('id', session.id)
          .style('background-color', getColor(session, config))
          .style('color', getTextColorByBackgroundColor(getColor(session, config)))
          .text(session.title);
      }
      else {
        timeslot.selectAll('.session')
          .data(sessions, d => d.id)
          .join('div')
            .attr('class', 'session')
            .style('background-color', d => getColor(d, config))
            .style('color', d => getTextColorByBackgroundColor(getColor(d, config)))
      }
    };
  };
}

function createDayCalendar(calendar, config, dayEvents) {

  const navigateToSession = (_ev, d) => {
    window.location = d.link;
  }

  calendar.selectAll(".session")
    .data(dayEvents)
    .join("div")
      .attr("class", "session")
      .attr('data-tippy-content', d => d.title)
      .style('grid-column', d => `${d.room}-start / auto`)
      .style('grid-row', d => `${d.timeStart} / ${d.timeEnd}`)
      .style('background-color', d => getColor(d, config))
      .style('color', d => getTextColorByBackgroundColor(getColor(d, config)))
      .on('click', navigateToSession)
      .on('keydown', (ev, d) => {
        if (ev.key === " " || ev.key === "Enter")
          navigateToSession(ev, d);
      })
      .text(d => d.title)
}

function populateDays(calendarSelection) {
  // NOTE: `dayData` is defined globally at top of file
  calendarSelection.selectAll('.day-slot')
    .data(dayData, d => d)
    .join("div")
      .attr("class", "day-slot")
      .style("grid-row", "tracks / auto")
      .style("grid-column", (_d, i) => `day-${i+1} / auto`)
      .append('h2')
        .append('a')
        .on('click', (ev, d) => {
          $(`.nav-pills a[href="#tab-${d.day}"]`).tab('show')
        })
        .text(d => d.text);
}

function populateRooms(calendarSelection, roomNames, day) {
  // TODO: use room names
  let roomData = [
    {'roomId': 'ok1', 'text': roomNames.ok1, 'link': 'room_ok1.html'},
    {'roomId': 'ok4', 'text': roomNames.ok4, 'link': 'room_ok4.html'},
    {'roomId': 'ok5', 'text': roomNames.ok5, 'link': 'room_ok5.html'},
    {'roomId': 'ok6', 'text': roomNames.ok6, 'link': 'room_ok6.html'},
    {'roomId': 'ok7', 'text': roomNames.ok7, 'link': 'room_ok7.html'},
    {'roomId': 'ok8', 'text': roomNames.ok8, 'link': 'room_ok8.html'},
    {'roomId': 'mistletoe', 'text': roomNames.mistletoe, 'link': 'room_mistletoe.html'},
    {'roomId': 'pinon', 'text': roomNames.pinon, 'link': 'room_pinon.html'}
  ];

  // truncate rooms added per-day (don't add unnecessary rooms we're not using)
  // switch (day) {
  //   case "Tuesday":
  //     roomData = roomData.slice(0, 5);
  //     break;
  //   case "Friday":
  //     roomData = roomData.slice(0, 7);
  //     break;
  // }

  populateHeader(calendarSelection, roomData);
}

function populateHeader(calendarSelection, data, isDay) {
  // Here's the problem - it's assuming the rooms are named "room1".  See the indexing here.
  let columnPosition = function(d, i) {
    if (isDay) {
      return `day-${(i+1)} / auto`;
    } else {
      return `${d.roomId} / auto`;
    }
  }

  calendarSelection.selectAll(".day-slot")
    .data(data, d => d)
    .join("div")
      .attr("class", "day-slot")
      .style("grid-row", "tracks / auto")
      .style("grid-column", columnPosition)
      .append('h2')
        .append('a')
        .attr('href', (d) => d.link)
        .text(d => d.text);
}

function populateTimes(calendarSelection) {
  let timeData = [
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

  calendarSelection.selectAll(".time-slot:not(.converted-timezone)")
    .data(timeData, d => d[0])
    .join("h2")
      .attr("class", "time-slot")
      .attr("data-time", d => d[1])
      .style("grid-row", d => d[1])
      .text(d => d[0]);

  calendarSelection.selectAll(".converted-timezone")
    .data(timeData, d => d[0])
    .join("h2")
      .attr("class", "time-slot converted-timezone")
      .attr("data-time", d => d[1])
      .style("grid-row", d => d[1])
      .text(d => d[0]);
}

function resetCalendar() {
  d3.selectAll('.session-group').remove();
  d3.selectAll('.session').remove();
}

function updateTimezone() {
  // get timezone
  const timezone = getTimezone();

  // apply timezone
  $('.converted-timezone').each((_, e) => {
    const element = $(e);
    const hourminutes = element.attr('data-time').split('-')[1];

    let time = moment(`2022-10-16 ${hourminutes.slice(0, 2)}:${hourminutes.slice(2, 4)} -05:00`, "YYYY-MM-DD HH:mm ZZ");

    const converted_date = time.clone().tz(timezone);
    let converted_time = converted_date.format("HH:mm");

    if (converted_date.format("DD") != time.format("DD"))
      converted_time += "<br>+1 day";

    element.html(converted_time);
  });
}

function getTextColorByBackgroundColor(hexColor) {
  hexColor = hexColor.replace("#", "");
  let r = parseInt(hexColor.substr(0, 2), 16);
  let g = parseInt(hexColor.substr(2, 2), 16);
  let b = parseInt(hexColor.substr(4, 2), 16);
  let yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
  return yiq >= 128 ? '#000000' : '#ffffff';
}

function getColor(d, config) {
  return config.calendar.colors[(d && d.eventType) || '---'];
}
