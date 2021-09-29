function finishCalendar(renderPromises) {
  updateKey();
  updateTzDropdown();

  renderPromises.push(updateFullCalendar());

  // only when everything has rendered do we update times in the calendar
  Promise.all(renderPromises).then(() => {
    updateTimezone();
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
    panel: "Tutorial / Panel",
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
    populateRooms(calendar);
    populateTimes(calendar);
  }
  else {
    populateDays(calendar);
    populateTimes(calendar);
  }

  // return deferred promise
  return $.when($.get('serve_config.json'), $.get(calendar_json))
    .done((config, events) => {
      if (day != null)
        createDayCalendar(calendar, config[0], events[0]);
      else
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
      const timePosition = sessions[0].timeStart + " / " + sessions[0].timeEnd;

      const timeslot = calendar.append('div')
        .style('grid-column', dayPosition)
        .style('grid-row', timePosition)
        .classed('session-group', sessions.length !== 1);

      if (sessions.length === 1) {
        const session = sessions[0];
        const session_color = config.calendar.colors[session.eventType];
        timeslot.attr('class', 'session')
          .attr('id', session.id)
          .style('background-color', session_color)
          .style('color', getTextColorByBackgroundColor(session_color))
          .text(session.title);
      }
      else {
        timeslot.selectAll('.session')
          .data(sessions, d => d.id)
          .join('div')
            .attr('class', 'session')
            .attr('data-toggle', 'popover')
            .attr('data-content', d => d.title)
            .style('background-color', d => config.calendar.colors[d.eventType])
            .style('color', d => getTextColorByBackgroundColor(config.calendar.colors[d.eventType]))
            // .text(d => d.title);
      }
    };
  };
}

function createDayCalendar(calendar, config, dayEvents) {
  const getColor = d => config.calendar.colors[d.eventType];
  const getTextColor = d => getTextColorByBackgroundColor(getColor(d));

  calendar.selectAll(".session")
    .data(dayEvents)
    .join("div")
      .attr("class", "session")
      .attr('data-toggle', 'popover')
      .attr('data-content', d => d.title)
      .style('grid-column', d => `room-${d.room}-start / auto`)
      .style('grid-row', d => `${d.timeStart} / ${d.timeEnd}`)
      .style('background-color', getColor)
      .style('color', getTextColor)
      .text(d => d.title)
}

function populateDays(calendarSelection) {
  let dayData = [
    "Sun, Oct 24",
    "Mon, Oct 25",
    "Tue, Oct 26",
    "Wed, Oct 27",
    "Thu, Oct 28",
    "Fri, Oct 29",
  ];

  populateHeader(calendarSelection, dayData, true /* isDay */);
}

function populateRooms(calendarSelection) {
  // TODO: use room names
  let roomData = [
    "Room 1",
    "Room 2",
    "Room 3",
    "Room 4",
    "Room 5",
    "Room 6",
    "Room 7",
  ];

  populateHeader(calendarSelection, roomData);
}

function populateHeader(calendarSelection, data, isDay) {
  let columnPosition = (_d, i) => `${(isDay ? 'day' : 'room')}-${i+1} / auto`;

  calendarSelection.selectAll(".day-slot")
    .data(data, d => d)
    .join("div")
      .attr("class", "day-slot")
      .style("grid-row", "tracks / auto")
      .style("grid-column", columnPosition)
      .append('h2')
        .text(d => d);
}

function populateTimes(calendarSelection) {
  let timeData = [
    ["7:30 AM", "time-0730"],
    ["8:00", "time-0800"],
    ["9:30", "time-0930"],
    ["10:00", "time-1000"],
    ["11:30", "time-1130"],
    ["12:00 PM", "time-1200"],
    ["1:30", "time-1330"],
    ["2:00 PM", "time-1400"],
    ["3:00", "time-1500"],
    ["3:30", "time-1530"],
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

    let time = moment(`2021-10-25 ${hourminutes.slice(0, 2)}:${hourminutes.slice(2, 4)} -05:00`, "YYYY-MM-DD HH:mm ZZ");

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
