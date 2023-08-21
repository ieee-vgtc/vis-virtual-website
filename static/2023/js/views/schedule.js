function addBookmarks() {
  // if(current_filter === "bookmarked sessions"){
  //   dayEvents = dayEvents.filter(d => d.bookmarked)
  // }

  let sessionsObj = d3.select(`#day`);

  let sessions = sessionsObj.selectAll(".session-listing")
    // .data(dayEvents)
  sessions.append('div')
    .attr('class', 'checkbox-bookmark fas')
    .classed('invisible', d => !d.bookmarked)
    .style('display', 'block')
    .style('position', 'absolute')
    .style('top', '-10px')
    .style('right', '10px')
    .html('&#xf02e;')
  sessions.append('div')
    .attr('class', 'bookmarks filter')
    .classed('invisible', d => !d.bookmarked)
    .style('display', 'block')
    .style('position', 'absolute')
    .style('top', '-2px')
    .style('right', '15px')
    .style('color', 'black')
    .text(d => d.bookmarks.length)
}

const getCalender = (renderPromises) => {
  return Promise.all([
    API.getPapers(),
    API.markGetAll(API.storeIDs.bookmarked)
  ]).then(
    ([papers, bookmarks]) => {

      //Gett all d3 elements with
      //For each

      // papers.forEach((paper) => {
      //   paper.UID = paper.UID;
      //   paper.bookmarked = bookmarks[paper.UID] || false;
      // });

      //Have to first get the current tab since all tabs have the same name

      Promise.all(renderPromises).then(() => {
        const bookmarkedPapers = papers.filter(d => d.bookmarked)


        let contentObj = d3.select(`.content`);
        let sessionsObj = contentObj.select(`.sessions`);
        let mobileContainer = contentObj.select(`.mobile-calender-container`);
        let rowObj = contentObj.selectAll('*:not(.session-listing-row).row')
        let sessions = contentObj.selectAll(".session-listing")

        sessions.each(function(d, i, nodeList)  {
          let currentSessionID = nodeList[i].classList[nodeList[i].classList.length-1]
          //filter papers by session
          let matching_sessions = []
          bookmarkedPapers.forEach(function(e) {
            const elClassList = nodeList[i].classList
            if(elClassList.contains(e.session_id)){
              matching_sessions.push(e)
            }
          })
          if(matching_sessions.length > 0){
            //the current session has some bookmarks, we should append a div
            d3.select(nodeList[i]).append('div')
              .attr('class', 'checkbox-bookmark fas selected')
              .style('display', 'block')
              .style('position', 'absolute')
              .style('top', '-10px')
              .style('right', '10px')
              .html('&#xf02e;')

            d3.select(nodeList[i]).append('div')
              .attr('class', 'bookmarks filter')
              // .classed('invisible', d => !d.bookmarked)
              .style('display', 'block')
              .style('position', 'absolute')
              .style('top', '-2px')
              .style('right', '15px')
              .style('color', 'black')
              // .text(d => d.bookmarks.length)
          } else  if (current_filter === "Bookmarked sessions"){
            contentObj.selectAll('.session-listing-row.'+currentSessionID).style('display', 'none')
          }
        })
        if(current_filter === "Bookmarked sessions") {
          //normal calender
          //mobile calender
          let timeslots = contentObj.selectAll('.timeslot-container.container')
          timeslots.each(function(d, i, nodeList) {
            let currentElement = d3.select(nodeList[i])
            let currentElement2 = currentElement.selectAll('.session-listing-row').filter(function() {
              if (this.style.display !== 'none') {
                noChild = false
              }
            });
            if (noChild) {
              d3.select(nodeList[i]).style('display', 'none')
            }
          })
        }

      });
    }
  )
}

