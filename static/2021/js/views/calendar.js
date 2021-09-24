function updateCalendar() {
  updateTzDropdown();
  updateTimezone();
  updateKey();
}

function getTimezone() {
  const urlTz = window.getUrlParameter && getUrlParameter('tz');
  if (urlTz) return urlTz;

  const storageTz = window.localStorage.getItem("tz")
  if (storageTz) return storageTz;

  return moment.tz.guess();
}

// ...promise fulfilled after cal is rendered.
function updateTzDropdown() {
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

function updateTimezone() {
  // get timezone
  const timezone = getTimezone();

  // apply timezone
  $('.converted-timezone').each((_, e) => {
    const element = $(e);
    const hourminutes = element.attr('data-time');

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
