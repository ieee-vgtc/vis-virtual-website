function make_cal(name) {

  const ref_tz = "UTC";

  return new Promise((resolve) => {
    // ...promise fulfilled after cal is rendered.

    const current_tz = getUrlParameter('tz') || window.localStorage.getItem(
      "tz") || moment.tz.guess();
    const tzNames = [...moment.tz.names()];

    const setupTZSelector = () => {
      const tzOptons = d3.select('#tzOptions')
      tzOptons.selectAll('option').data(tzNames)
        .join('option')
        .attr('data-tokens', d => d.split("/").join(" "))
        .text(d => d)
      $('.selectpicker')
        .selectpicker('val', current_tz)
        .on('changed.bs.select',
          function (e, clickedIndex, isSelected, previousValue) {
            new_tz = tzNames[clickedIndex];

            const localStorage = window.localStorage;
            localStorage.setItem("tz", new_tz);

            window.open(window.location.pathname + '?tz=' + new_tz, '_self');
          })

      $("#saveTz").on('click', function (_) {
        const new_tz = $(".selectpicker").val();

        const localStorage = window.localStorage;
        localStorage.setItem("tz", new_tz);

        window.open(window.location.pathname + '?tz=' + new_tz, '_self');
      });

      $("#resetTz").on('click', function (_) {
        const localStorage = window.localStorage;
        localStorage.removeItem("tz");
        window.open(window.location.pathname, '_self');
      });
    }

    setupTZSelector();

    // requires moments.js
    const enumerateDaysBetweenDates = function (startDate, endDate) {
      const dates = [];


      const currDate = moment(startDate).tz(ref_tz);
      const lastDate = moment(endDate).tz(ref_tz);

      dates.push(currDate.clone().toDate());
      while (currDate.add(1, 'days').diff(lastDate) < 0) {
        dates.push(currDate.clone().toDate());
      }

      dates.push(lastDate.toDate());
      return dates;
    };


    $.get('serve_config.json').then(config => {
      $.get(name).then(events => {

        events.forEach(e => e.raw = e);

        const all_cals = [];
        const timezoneName = current_tz;

        const min_date = d3.min(
          events.map(e => moment(e.start).tz(ref_tz).format()));

        // var min_hours = d3.min(
        //   events.map(e => moment(e.start).tz(ref_tz).hours()));
        // var max_hours = d3.max(
        //   events.map(e => moment(e.end).tz(ref_tz).hours()));
        // if (min_hours < 0 || max_hours > 24) {
        //   min_hours = 0;
        //   max_hours = 24;
        // }

        // manually set the offsets for the calendar based on GMT
        const min_hours = 6+6;
        const max_hours = 17+6;

        const middleDay = moment(min_date).add(3, 'days');

        let renderAllTexts = false;
        let timeDayReference = middleDay.format("YYYY-MM-DD");
        const Calendar = tui.Calendar;
        const calendar = new Calendar('#calendar', {
          defaultView: 'week',
          isReadOnly: true,
          // useDetailPopup: true,
          taskView: false,
          scheduleView: ['time'],
          usageStatistics: false,
          week: {
            startDayOfWeek: 7, // IEEE VIS starts on Saturday
            workweek: !config.calendar["sunday_saturday"],
            hourStart: min_hours,
            hourEnd: max_hours
          },
          timezones: [{
            timezoneOffset: 0, //all dates in GMT
            displayLabel: timezoneName,
            tooltip: timezoneName
          }],
          template: {
            monthDayname: function (dayname) {
              return '<span class="calendar-week-dayname-name">' + dayname.label + '</span>';
            },
            time: function (schedule) {
              return (schedule.calendarId === 'vis' || schedule.calendarId === 'memorial' ||
                schedule.calendarId == "keynote" || schedule.calendarId == "capstone" || renderAllTexts) ? '<strong>' + moment(
                schedule.raw.realStart)
                .tz(timezoneName)
                .format('HH:mm') + '</strong> ' + schedule.title : '';
            },
            timegridCurrentTime: function(x) {
              return moment(new Date(x.hourmarker))
                .tz(timezoneName)
                .format("HH:mm");
            },
            timegridDisplayPrimaryTime: function (x) {
              const cDate = timeDayReference + ` ${x.hour}:00`
              const timeRef = moment.tz(cDate, ref_tz);
              const newTime = timeRef.clone().tz(timezoneName)
              let ret = newTime.hour();
              const dayDiff = newTime.date() - timeRef.date()

              // if the current time is in DST and the target time is not (or vice versa), tweak hour offset
              // NOTE: currently only supports 1 hour offsets; 2 hour offsets exist
              const timezoneDiff = new Date().getTimezoneOffset() - newTime.toDate().getTimezoneOffset();
              if (timezoneDiff === 60) ret -= 1;
              if (timezoneDiff === -60) ret += 1;

              return (dayDiff !== 0 ? (dayDiff > 0 ? '+' + dayDiff : dayDiff) + 'd ' : '') + ret + ':00'
            },
            milestone: function (schedule) {
              return '<span class="calendar-font-icon ic-milestone-b"></span> <span style="background-color: ' + schedule.bgColor + '"> M: ' + schedule.title + '</span>';
            },
            weekDayname: function (model) {
              const parts = model.renderDate.split('-');
              return '<span class="tui-full-calendar-dayname-name"> ' + parts[1] + '/' + parts[2] + '</span>&nbsp;&nbsp;<span class="tui-full-calendar-dayname-name">' + model.dayName + '</span>';
            },
          },
        });
        calendar.setDate(Date.parse(min_date));
        calendar.createSchedules(events);
        calendar.on({
          'clickSchedule': function (e) {
            const s = e.schedule
            if (s.location.length > 0) {
              window.open(s.location, '_blank');
            }
          },
        })

        all_cals.push(calendar);

        const cols = config.calendar.colors;
        if (cols) {
          const cals = [];
          Object.keys(cols).forEach(k => {
            const v = cols[k];
            cals.push({
              id: k,
              name: k,
              color: getTextColorByBackgroundColor(v),
              bgColor: v,
            })
          })

          calendar.setCalendars(cals);
        }

        // let week_dates = enumerateDaysBetweenDates(
        //   // calendar.getDateRangeStart().toDate(),
        //   // calendar.getDateRangeEnd().toDate()
        //   "2020-10-25", "2020-10-30"
        // );

        // manually set the dates
        let week_dates = [
          "2020-10-25",
          "2020-10-26",
          "2020-10-27",
          "2020-10-28",
          "2020-10-29",
          "2020-10-30"
        ];

        // drop the last day (conference is 6 days)
        week_dates = week_dates.slice(0, 6);
        console.log(week_dates,"--- week_dates");
        let i = 1;
        for (const day of week_dates) {
          const cal = new Calendar('#cal__' + i, {
            defaultView: 'day',
            isReadOnly: true,
            // useDetailPopup: true,
            taskView: false,
            scheduleView: ['time'],
            usageStatistics: false,

            week: {
              startDayOfWeek: 7, // IEEE VIS starts on Sunday
              workweek: !config.calendar["sunday_saturday"],
              hourStart: min_hours,
              hourEnd: max_hours
            },
            timezones: [{
              timezoneOffset: 0, // GMT is ref
              displayLabel: timezoneName,
              tooltip: timezoneName
            }],
          })

          cal.setDate(day); // give TUI a string; it'll parse and pick the day for the locale
          const daysEvents = events.filter(e => e.start.split("T")[0] === day);
          cal.createSchedules(daysEvents);
          cal.on({
            'clickSchedule': function (e) {
              const s = e.schedule
              if (s.location.length > 0) {
                window.open(s.location, '_blank');
              }
            },
          })

          const cols = config.calendar.colors;
          if (cols) {
            const cals = [];
            Object.keys(cols).forEach(k => {
              const v = cols[k];
              cals.push({
                id: k,
                name: k,
                color: getTextColorByBackgroundColor(v),
                bgColor: v,
              })
            })

            cal.setCalendars(cals);
          }

          all_cals.push(cal);
          i++;
        }

        function render(all_cals) {
          all_cals.forEach(c => {
            if (c === calendar) {
              timeDayReference = middleDay.format("YYYY-MM-DD");
              renderAllTexts = false
            } else {
              renderAllTexts = true
            }
            c.render(true)
          });

          // bind tooltip to all calendar events
          $('.tui-full-calendar-time-schedule').tooltip({
            title: function () {
              let scheduleId = this.getAttribute("data-schedule-id");
              let calendarId = this.getAttribute("data-calendar-id");
              let foundEvent;
              all_cals.some(cal => {
                foundEvent = cal.getSchedule(scheduleId, calendarId);
                return !!foundEvent;
              });

              if (foundEvent) {
                return foundEvent.title;
              }
            },
          });
        }

        // force render:
        render(all_cals);

        // ***  PROMISE FULFILLED *** //
        resolve({
          render: () => render(all_cals),
        });

        // finally, render a color legend
        const itemMapping = {
          vis: "Conference",
          paper: "Papers",
          associated: "Associated Events / Symposium",
          workshop: "Workshop",
          application: "Application Spotlights",
          panel: "Tutorial / Panel",
        };

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
      })

    })
  })

}

function getTextColorByBackgroundColor(hexColor) {
  hexColor = hexColor.replace("#", "");
  let r = parseInt(hexColor.substr(0, 2), 16);
  let g = parseInt(hexColor.substr(2, 2), 16);
  let b = parseInt(hexColor.substr(4, 2), 16);
  let yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
  return yiq >= 128 ? '#000000' : '#ffffff';
}
