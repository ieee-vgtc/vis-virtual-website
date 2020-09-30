function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
};

function setQueryStringParameter(name, value) {
    // console.log("name", name, "value", value);
    const params = new URLSearchParams(window.location.search);
    params.set(name, value);
    window.history.replaceState({}, "", decodeURIComponent(`${window.location.pathname}?${params}`));
}

function formatDate(id,dat){
  var hid = $("#"+id)

  const current_tz = getUrlParameter('tz') || moment.tz.guess();

  let atime = moment(dat).clone().tz(current_tz)

  hid.html("<span>"+atime.format("MMMM, Do MMM YYYY")+":</span>")

}

function formatDateTime(id,start,end){
  var hid = $("#"+id)

  const current_tz = getUrlParameter('tz') || moment.tz.guess();

  let starttime = moment(start).clone().tz(current_tz)
  let endtime = moment(end).clone().tz(current_tz)

  //if(starttime.diff(endtime, "days") <= 0) // Making difference between the "D" numbers because the diff function
                                             // seems like not considering the timezone
  if(starttime.format("D") == endtime.format("D"))
    hid.html("<span>"+starttime.format("hh:mm A")+"</span>&ndash;<span>"+endtime.format("hh:mm A")+"</span>")
  else
    hid.html("<span>"+starttime.format("MMM Do hh:mm A")+"</span>&ndash;<span>"+endtime.format("MMM Do hh:mm A")+"</span>")
  
}

const initTypeAhead = (list, css_sel, name, callback) => {
    const bh = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        local: list,
        sufficient: 20,
        identify: function(obj) { return obj; },

    });
    function bhDefaults(q, sync) {

        if (q === '' && name == 'session') {
            sync(bh.all()); // This is the only change needed to get 'ALL' items as the defaults
        }

        else {
            bh.search(q, sync);
        }
    }


    // remove old
    $(css_sel).typeahead('destroy')
      .off('keydown')
      .off('typeahead:selected')
      .val('');

    $(css_sel).typeahead({
          hint: true,
          highlight: true, /* Enable substring highlighting */
        minLength: 0, /* Specify minimum characters required for showing suggestions */
        limit:20
      },
      {name, source: bhDefaults})
      .on('keydown', function (e) {
          if (e.which === 13) {
              // e.preventDefault();
              callback(e, e.target.value);
              $(css_sel).typeahead('close');
          }
      })
      .on('typeahead:selected', function (evt, item) {
          callback(evt, item)
      })

    $(css_sel + '_clear').on('click', function () {
        $(css_sel).val('');
        callback(null, '');
    })
}

const setTypeAhead = (subset, allKeys,filters, render) => {

    Object.keys(filters).forEach(k => filters[k] = null);

    initTypeAhead(allKeys[subset], '.typeahead_all', subset,
                  (e, it) => {
                      setQueryStringParameter("search", it);
                      filters[subset] = it.length > 0 ? it : null;
                      render();
                  });
}


let calcAllKeys = function (allPapers, allKeys) {
    const collectAuthors = new Set();
    const collectKeywords = new Set();
    const collectSessions = new Set();

    allPapers.forEach(
      d => {
          d.content.authors.forEach(a => collectAuthors.add(a));
          d.content.keywords.forEach(a => collectKeywords.add(a));
          d.content.session.forEach(a => collectSessions.add(a));
          allKeys.titles.push(d.content.title);
      });
    allKeys.authors = Array.from(collectAuthors);
    allKeys.keywords = Array.from(collectKeywords);
    allKeys.session = Array.from(collectSessions);
    allKeys.session.sort();
};
