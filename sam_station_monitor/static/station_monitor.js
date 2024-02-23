
function HTMLescape(html){
    return document.createElement('div')
        .appendChild(document.createTextNode(html))
        .parentNode
        .innerHTML
}


var time_format = d3.time.format("%Y-%m-%d %H:%M:%S");

$( document ).ready(function() {
 // update times to browser local time
 $("span[data-timestamp]").each(function( index ) {
  var d = new Date($(this).data('timestamp'));
  $(this).text(time_format(d));
 });

 // reveal the content (the graphs may not have been drawn yet as they are asynchronous)
 $('#loadingMask').fadeOut();

});

function plot_histo(data, target, width, height, title, xlabel) {
var margin = {top: 40, right: 20, bottom: 40, left: 60},
    width = width - margin.left - margin.right,
    height = height - margin.top - margin.bottom;

var x = d3.scale.linear()
    .range([0, width]);

var y = d3.scale.linear()
    .range([height, 0]);

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");


var svg = make_plot_area(target, width, height, margin);

  if (data.length > 0) {
    x.domain([0, d3.max(data)]).nice();
  } else x.domain([0,1]);

  var histo = d3.layout.histogram().bins(x.ticks())(data);

  y.domain([0, d3.max(histo, function(d) { return d.y; })]).nice();

  svg.selectAll(".bar")
      .data(histo)
    .enter().append("rect")
      .attr("class", "bar")
      .attr("x", function(d) { return x(d.x); })
      .attr("width", function(d) { return x(d.dx) + 1;})
      .attr("y", function(d) { return y(d.y); })
      .attr("height", function(d) { return height - y(d.y); });

  svg.append("g")
      .attr("class", "axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)
    .append("text")
      .attr("x", width / 2 )
      .attr("y",  margin.bottom)
      .attr("dy", -5)
      .style("text-anchor", "middle")
      .text(xlabel);

  svg.append("g")
      .attr("class", "axis")
      .call(yAxis)
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -margin.left)
      .attr("x", -height/2)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text("Frequency");


  svg.append("text")
          .attr("x", (width / 2))             
          .attr("y", 0 - (margin.top / 2))
          .attr("text-anchor", "middle")  
          .attr("class", "title")
          .text(title);
}

// 24 hour time format
var graph_time_format = d3.time.format.multi([
  [".%L", function(d) { return d.getMilliseconds(); }],
  [":%S", function(d) { return d.getSeconds(); }],
  ["%H:%M", function(d) { return d.getMinutes(); }],
  ["%H", function(d) { return d.getHours(); }],
  ["%a %d", function(d) { return d.getDay() && d.getDate() != 1; }],
  ["%b %d", function(d) { return d.getDate() != 1; }],
  ["%B", function(d) { return d.getMonth(); }],
  ["%Y", function() { return true; }]
]);

function delivery_plot(data, width, timerange) {
var target = "#delivery_plot";
var height = 500;
var margin = {top: 50, right: 20, bottom: 40, left: 60},
width = width - margin.left - margin.right;
height = height - margin.top - margin.bottom;

var deliverytimes = [];
var closetimes = [];
var starttime = Number.MAX_VALUE;
data.forEach(function(p) {
  if (p.start_time < starttime) starttime = p.start_time;
  p.files.forEach(function(f) {
    deliverytimes.push(f.open_time);
    if (f.close_time) closetimes.push(f.close_time);
  })
});

// add the start time as the first entry of the delivery time array to act as the zero value
// if a file has been delivered use that as the zero for the close time array
deliverytimes = deliverytimes.sort(function(a,b) { return a-b;} );
deliverytimes.unshift(starttime);
closetimes = closetimes.sort(function(a,b) { return a-b;} );
if (deliverytimes.length > 1) {
  closetimes.unshift(deliverytimes[1]);
} else {
  closetimes.unshift(starttime);
}

var deliverylinedata = d3.zip(deliverytimes, d3.range(0, deliverytimes.length));
var closelinedata = d3.zip(closetimes, d3.range(0, closetimes.length));

var x = d3.time.scale()
    .range([0, width])
    .domain(timerange);

var y = d3.scale.linear()
    .range([height, 0])
    .domain([0, deliverytimes.length >1 ? deliverytimes.length-1 : 1]).nice();

var xAxis = d3.svg.axis()
    .scale(x)
    .tickFormat(graph_time_format)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

var svg = d3.select(target).append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

svg.append("g")
      .attr("class", "axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)
      .append("text")
      .attr("x", width / 2 )
      .attr("y",  margin.bottom)
      .attr("dy", -5)
      .style("text-anchor", "middle")
      .text("Time");

svg.append("g")
      .attr("class", "axis")
      .call(yAxis);

var line = d3.svg.line()
    .interpolate('step-after')
    .x(function(d) { return x(d[0]); })
    .y(function(d) { return y(d[1]); });

svg.append("path")
      .datum(deliverylinedata)
      .attr("class", "delivered")
      .attr("d", line);

svg.append("path")
      .datum(closelinedata)
      .attr("class", "closed")
      .attr("d", line);

  var colors = [ {label:"Files opened", cls:"delivered"}, { label:"Files closed", cls: "closed"} ]
  var legend = svg.append("g")
      .attr("class", "legend");

  var legendText = legend.selectAll('text').data(colors);
  legendText.enter()
      .append("text")
      .text(function(d, i) { return d.label; })
      .attr("x", function(d, i) { var offset = i>0 ? colors[i-1].offset + colors[i-1].textwidth : 0;
                                  var size = this.getComputedTextLength(); 
                                  d.textwidth = size;
                                  d.offset = offset;
                                  return i*60 + 30 + offset; })
      .attr("y", 0)
      ;

  var legendRect = legend.selectAll('line').data(colors);
  legendRect.enter()
      .append("line")
      .attr("x1", function(d, i) { return i*60 + d.offset; })
      .attr("x2", function(d, i) { return i*60 + d.offset + 20; })
      .attr("y1", -4)
      .attr("y2", -4)
      .attr("class", function(d, i) { return d.cls; })
;
  if(legend.node()) {
    var bbox = legend.node().getBBox();
    legend.attr("transform", "translate(" + ((width-bbox.width) / 2) + ",-10)");
  }
  svg.append("text")
          .attr("x", (width / 2))             
          .attr("y", -35 )
          .attr("text-anchor", "middle")  
          .attr("class", "title")
          .text("Files opened and closed");

}

function sausage_plot(data, width, timerange) {

var target = "#process_plot";
var height;
if (data.length <= 10) height = 40*data.length; // set the height from the number of processes
else if (data.length <= 1000) height = Math.floor( 40 - 30*data.length/(1000-10))*data.length;
else height = 10*data.length
// in this case the height excludes margins, but the width does not
var margin = {top: 50, right: 20, bottom: 40, left: 60},
    width = width - margin.left - margin.right;

var x = d3.time.scale()
    .range([0, width])
    .domain(timerange);

var y = d3.scale.ordinal()
    .rangeBands([height, 0], 0.1);

var xAxis = d3.svg.axis()
    .scale(x)
    .tickFormat(graph_time_format)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

// tooltip div
var tooltip = d3.select(target).append("div")   
    .attr("class", "tooltip")               
    .style("opacity", 0);

// the plot
var svg = d3.select(target).append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var current_time = new Date();

var process_ids = data.map(function(d) { return d.process_id; });;

// sort the process ids in order for display
process_ids.sort(function(a, b) { return b-a;});

y.domain(process_ids);

  svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)
      .append("text")
      .attr("x", width / 2 )
      .attr("y",  margin.bottom)
      .attr("dy", -5)
      .style("text-anchor", "middle")
      .text("Time");

  svg.append("g")
      .attr("class", "y axis")
      .call(yAxis);

  function make_process_tooltip(d) {
     tooltip.transition()
       .duration(200)
       .style("opacity", 0.9);

    var element = document.createElement('div');
    // lookup the description by id - this isn't very efficient
    for (var i=0 ;i<data.length; ++i) {
      if (data[i].process_id==d) {
        element.appendChild(document.createTextNode(data[i].node_name));
        element.appendChild(document.createElement('br'));
        element.appendChild(document.createTextNode(data[i].description));
        break;
      }
    }
    tooltip.html(element.innerHTML)
           .style("left", (d3.event.pageX) + "px")
           .style("top", (d3.event.pageY) + "px");

    return element;
  }

  d3.selectAll('.y.axis>.tick')
      .on("mouseover", make_process_tooltip)
       .on("mouseout", hide_tooltip);

// for each process, translate to the appropriate vertical slot
var proc = svg.selectAll(".proc")
      .data(data)
      .enter().append("g")
      .attr("class", "g")
      .attr("transform", function(d) { return "translate(0," + y(d.process_id) + ")"; })
      .attr("class", function(d) { return d.status; });

proc.append("line")
      .attr("x1", function(d) { return x(d.start_time); } )
      .attr("x2", function(d) { return x(d.end_time ? d.end_time : current_time); } )
      .attr("y1", y.rangeBand()/2)
      .attr("y2", y.rangeBand()/2)
      .attr("stroke-width", 1);

// draw the transfer file boxes

function make_file_tooltip(d, status) {
   tooltip.transition()
     .duration(200)
     .style("opacity", 0.9);

  var formatTime = d3.time.format("%Y-%m-%d %H:%M:%S");
  var element = document.createElement('div');
  var br = document.createElement('br');
  element.appendChild(document.createTextNode(d.file_name));
  element.appendChild(br.cloneNode());
  element.appendChild(document.createTextNode("Status: " + (status ? status : d.status)));
  element.appendChild(br.cloneNode());
  element.appendChild(document.createTextNode("Opened at: " + formatTime(new Date(d.open_time))));
  if (d.transfer_time) {
    element.appendChild(br.cloneNode());
    element.appendChild(document.createTextNode("Transfer completed at: " + formatTime(new Date(d.transfer_time))));
  }
  if (d.close_time) {
    element.appendChild(br.cloneNode());
    element.appendChild(document.createTextNode("Closed at: " + formatTime(new Date(d.close_time))));
  }
  if (d.waited_for) {
    element.appendChild(br.cloneNode());
    var t = "Waited for: ";
    if (d.waited_for < 600) t += d.waited_for.toFixed(2) + "s";
    else t += (d.waited_for/60).toFixed(2) +"min";
    element.appendChild(document.createTextNode(t));
  }
  if (d.transfer_time) {
    var xfer_time = (d.transfer_time - d.open_time)/1000;
    element.appendChild(br.cloneNode());
    var t = "Transferred in: ";
    if (xfer_time < 600) t += xfer_time.toFixed(2) + "s";
    else t += (xfer_time/60).toFixed(2) +"min";
    element.appendChild(document.createTextNode(t));
  }
  if (d.busy_for) {
    element.appendChild(br.cloneNode());
    var t = "Busy for: "
    if (d.busy_for < 600) t += d.busy_for.toFixed(2) + "s";
    else t += (d.busy_for/60).toFixed(2) +"min";
    element.appendChild(document.createTextNode(t));
  }
   tooltip.html(element.innerHTML)
          .style("left", (d3.event.pageX) + "px")
          .style("top", (d3.event.pageY) + "px");

  return element;
}
function hide_tooltip() {
   tooltip.transition()
          .duration(500)
          .style("opacity", 0);
}

proc.selectAll("xfer")
      .data(function(d) { return d.files; })
      .enter().append("rect")
      .filter(function(d) { return Boolean(d.transfer_time);})
      .attr("x", function(d) { return x(d.open_time); })
      .attr("width", function(d) {
        return (x(d.transfer_time) - x(d.open_time));
      })
      .attr("height", y.rangeBand())
      .attr("class", function(d) { return "intransfer"; })
      .on("mouseover", function (d) {
         make_file_tooltip(d, "in transfer");
         })
       .on("mouseout", function(d) {
         hide_tooltip();
         });

proc.selectAll("process")
      .data(function(d) { return d.files; })
      .enter().append("rect")
      .attr("x", function(d) { return x(d.transfer_time ? d.transfer_time : d.open_time); })
      .attr("width", function(d) {
        var start = d.transfer_time ? d.transfer_time : d.open_time;
        var end = d.close_time ? d.close_time : current_time;
        return (x(end) - x(start));
      })
      .attr("height", y.rangeBand())
      .attr("class", function(d) {
        if(d.completed_time){ return "consumed"; }
        else { return d.status; }
      })
      .on("mouseover", function (d) {
         make_file_tooltip(d);
         })
       .on("mouseout", function(d) {
         hide_tooltip();
         });

function make_file_completed_tooltip(d, status) {
   tooltip.transition()
     .duration(200)
     .style("opacity", 0.9);

  var formatTime = d3.time.format("%Y-%m-%d %H:%M:%S");
  var element = document.createElement('div');
  var br = document.createElement('br');
  element.appendChild(document.createTextNode(d.file_name));
  element.appendChild(br.cloneNode());
  element.appendChild(document.createTextNode("Status: completed"));
  element.appendChild(br.cloneNode());
  element.appendChild(document.createTextNode("Opened at: " + formatTime(new Date(d.open_time))));
  element.appendChild(br.cloneNode());
  element.appendChild(document.createTextNode("Closed at: " + formatTime(new Date(d.close_time))));
  element.appendChild(br.cloneNode());
  element.appendChild(document.createTextNode("Completed at: " + formatTime(new Date(d.completed_time))));
  tooltip.html(element.innerHTML)
         .style("left", (d3.event.pageX) + "px")
         .style("top", (d3.event.pageY) + "px");

  return element;
}

// TODO: Create a tooltip for the lines
// Draw the vertical line marking file completion time.
proc.selectAll("process")
        .data(function(d) { return d.files; })
        .enter().append("line")
        .filter(function(d) { return Boolean(d.completed_time);})
        .attr('x1', function(d) { return x(d.completed_time); } )
        .attr('y1', y.rangeBand())
        .attr('x2', function(d) { return x(d.completed_time); } )
        .attr('y2', y.rangeBand()- y.rangeBand() )
        .style("stroke-width", 2)
        .on("mouseover", function (d) {
           make_file_completed_tooltip(d, "completed");
           })
         .on("mouseout", function(d) {
           hide_tooltip();
           });

// Create the legend
  var colors = [ 
                { label:"In transfer/available", cls: "intransfer"},
                { label:"Transferred", cls:"transferred"},
                { label:"Completed", cls:"completed"},
                { label:"Consumed", cls:"consumed"},
                { label:"Skipped", cls:"skipped"},
                { label:"Failed", cls:"failed"},
                { label:"Cancelled", cls:"cancelled"},
                { label:"Unknown", cls:"unknown"}
  ];

  var legend = svg.append("g")
      .attr("class", "legend");

  var legendText = legend.selectAll('text').data(colors);
  legendText.enter()
      .append("text")
      .text(function(d, i) { return d.label; })
      .attr("x", function(d, i) { var offset = i>0 ? colors[i-1].offset + colors[i-1].textwidth : 0;
                                  var size = this.getComputedTextLength(); 
                                  d.textwidth = size;
                                  d.offset = offset;
                                  return i*40 + 20 + offset; })
      .attr("y", 0)
      ;

  var legendRect = legend.selectAll('rect').data(colors);
  legendRect.enter()
      .append("rect")
      .attr("width", 10)
      .attr("height", 10)
      .attr("x", function(d, i) { return i*40 + d.offset; })
      .attr("y", -10)
      .attr("class", function(d, i) { return d.cls; })
;
  if(legend.node()) {
    var bbox = legend.node().getBBox();
    legend.attr("transform", "translate(" + ((width-bbox.width) / 2) + ",-10)");
  }
  svg.append("text")
          .attr("x", (width / 2))             
          .attr("y", 0 - 35)
          .attr("text-anchor", "middle")  
          .attr("class", "title")
          .text("File activity by process");
}

function n_processes_plot(data, width, timerange) {

var target = "#process_plot";
var height = 500;

var margin = {top: 50, right: 20, bottom: 40, left: 60},
    width = width - margin.left - margin.right;
    height = height - margin.top - margin.bottom;

  // massage the data. This requires two passes; first to compute the changes at each time,
  // then sort the events in order and compute the absolute values

  var events = [];
  var max_procs = 0;
  var current_time = new Date();
  var still_running = false;
  data.forEach(function(d) {
    // this is a process
    events.push( { "t" : d.start_time, "nprocs" : 1, "nbusy" : 0, "ntransfer" : 0 } );
    if (d.end_time) events.push( { "t" : d.end_time, "nprocs" : -1 } );
    else still_running = true;
    d.files.forEach(function(f) {
      // these are the files
      // we have to try and handle the case where the user is not updating transfer times
      // so always show an open file with no close as being in transfer - if they aren't logging
      // transfers this will be the current open file, so colouring it differently is okay
      events.push( { "t" : f.open_time, "nbusy" : 1 } );
      if (f.transfer_time) {
        events.push( { "t" : f.open_time, "ntransfer" : 1 } );
        events.push( { "t": f.transfer_time, "ntransfer" : -1});
      } else {
        if (!f.close_time) events.push( { "t" : f.open_time, "ntransfer" : 1 } );
      }
      if (f.close_time) {
        events.push( { "t" : f.close_time, "nbusy" : -1 } );
      }
    });
  });

  // if anything is still running, the endpoint of the plot should be now
  if (still_running) events.push( { "t" : current_time, "nprocs" : 0, "nbusy" : 0, "ntransfer" : 0 });

  if (events.length > 0 ) {
    events = events.sort(function(a,b) { return a.t - b.t; } );
    var nprocs = [ { "t" : timerange[0], "n" : 0 } ]
    var ntransfer = [ { "t" : timerange[0], "n" : 0 } ]
    var nbusy = [ { "t" : timerange[0], "n" : 0 } ]

    events.forEach(function(d) {
      if (d.nprocs != undefined) {
        var n = nprocs[nprocs.length-1].n + d.nprocs;
        if (n > max_procs) max_procs = n;
        nprocs.push({ "t" : d.t, "n": n});
      }
      if (d.ntransfer != undefined) ntransfer.push({ "t" : d.t, "n" : ntransfer[ntransfer.length-1].n + d.ntransfer});
      if (d.nbusy != undefined) nbusy.push( { "t" : d.t, "n": nbusy[nbusy.length-1].n + d.nbusy});
    });
  } else {
    var ntransfer = [];
  }

var x = d3.time.scale()
    .range([0, width])
    .domain(timerange);
var xAxis = d3.svg.axis()
    .scale(x)
    .tickFormat(graph_time_format)
    .orient("bottom");

var y = d3.scale.linear()
    .range([height, 0])
    .domain([0, max_procs]).nice();
var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

  // drop events since it may be large and we no longer need it
  events = undefined;

  var line = d3.svg.line()
    .interpolate('step-after')
    .x(function(d) { return x(d.t); })
    .y(function(d) { return y(d.n); });

  var area = d3.svg.area()
      .x(function(d) { return x(d.t); })
      .y0( y(0) )
      .y1(function(d) { return y(d.n); })
      .interpolate('step-after')

  var target = "#n_processes_plot";
  svg = make_plot_area(target, width, height, margin);

  svg.append("path")
     .datum(nbusy)
     .attr("class", "nbusy")
     .attr("d", area);

  // only plot transfers if there is anything
  if (ntransfer.length > 0) {
    svg.append("path")
       .datum(ntransfer)
       .attr("class", "ntransfer")
       .attr("d", area);
  }

  svg.append("path")
     .datum(nprocs)
     .attr("class", "nprocesses")
     .attr("d", line);

  svg.append("g")
      .attr("class", "axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)
      .append("text")
      .attr("x", width / 2 )
      .attr("y",  margin.bottom)
      .attr("dy", -5)
      .style("text-anchor", "middle")
      .text("Time");

  svg.append("g")
      .attr("class", "axis")
      .call(yAxis)
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -margin.left)
      .attr("x", -height/2)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text("Number of processes");

  var colors = [ {label:"Idle", cls:"nidle"}, { label:"Transferring", cls: "ntransfer"}, {label:"Busy", cls:"nbusy"} ];

  var legend = svg.append("g")
      .attr("class", "legend");

  var legendText = legend.selectAll('text').data(colors);
  legendText.enter()
      .append("text")
      .attr("y", 0)
      .text(function(d, i) { return d.label; })
      .attr("x", function(d, i) { var offset = i>0 ? colors[i-1].offset + colors[i-1].textwidth : 0;
                                  var size = this.getComputedTextLength(); 
                                  d.textwidth = size;
                                  d.offset = offset;
                                  return 10 + i*40 + 20 + offset; })
      ;

  var legendRect = legend.selectAll('rect').data(colors);
  legendRect.enter()
      .append("rect")
      .attr("width", 10)
      .attr("height", 10)
      .attr("x", function(d, i) { return 10 + i*40 + d.offset; })
      .attr("y", -10)
      .attr("class", function(d, i) { return d.cls; })
;
  if (legend.node()) {
  var bbox = legend.node().getBBox();
  legend.attr("transform", "translate(" + ((width-bbox.width) / 2) + ",-10)");
  }

  svg.append("text")
          .attr("x", (width / 2))             
          .attr("y", -35)
          .attr("text-anchor", "middle")  
          .attr("class", "title")
          .text("Total and busy processes");
}

function make_project_plots(source) {
  d3.json(source, function(error, data) {
    // get all the wait and busy times
    var waittimes = [], transfertimes = [], busytimes = [];
    data.forEach(function(d) {
      d.files.forEach(function(d2) {
        if (d2.waited_for) waittimes.push(d2.waited_for/60);
        if (d2.transferred_for) transfertimes.push(d2.transferred_for/60);
        if (d2.busy_for) busytimes.push(d2.busy_for/60);
      })
    });
    plot_histo(waittimes, "#waittimes_plot", 500, 500, "Wait time per file", "Wait time (min)");
    plot_histo(transfertimes, "#transfertimes_plot", 500, 500, "Transfer time per file", "Transfer time (min)");
    plot_histo(busytimes, "#busytimes_plot", 500, 500, "Busy time per file", "Busy time (min)");

    // get all the start end times to calculate the range
    // do this here so multiple plots can use the same range
    var times = [];
    var current_time = new Date();
    data.forEach(function(d) {
       times.push(d.start_time);
       if (d.end_time) times.push(d.end_time);
       else times.push(current_time);
    });
    var timerange = d3.extent(times);
    // make some clear space at the beginning
    timerange[0] = timerange[0] - (timerange[1] - timerange[0])*0.05;

    delivery_plot(data, 1000, timerange);
    n_processes_plot(data, 1000, timerange);
    sausage_plot(data, 1000, timerange);

});

}

function make_top_level_plots(source) {
 d3.json(source, function(error, data) {
  var height = 250, width = 500;

  var margin = {top: 40, right: 20, bottom: 40, left: 60},
      width = width - margin.left - margin.right,
      height = height - margin.top - margin.bottom;

  var x = d3.time.scale()
    .range([0, width]);

  var y = d3.scale.linear()
      .range([height, 0]);

  var xAxis = d3.svg.axis()
      .scale(x)
      .tickFormat(graph_time_format)
      .orient("bottom");
  var yAxis = d3.svg.axis()
      .scale(y)
      .orient("left");

  // format the data more conveniently
  data.forEach(function(d) {
    d.tm = d[0], d.nwaiting = d[1], d.nactive = d[2], d.medianwait = d[3];
    if (d.nwaiting + d.nactive > 0) d.pcwaiting = ( 100*d.nwaiting/(d.nwaiting+d.nactive) );
    else d.pcwaiting = null;
  });  

  var target = "#process_wait_history";
  svg = make_plot_area(target, width, height, margin);

  x.domain(d3.extent(data, function(d) { return d.tm; }));

  svg.append("g")
      .attr("class", "axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)
      .append("text")
      .attr("x", width / 2 )
      .attr("y",  margin.bottom)
      .attr("dy", -5)
      .style("text-anchor", "middle")
      .text("Time");

  y.domain(d3.extent(data, function(d) { return d.pcwaiting; })).nice();

  svg.append("g")
      .attr("class", "axis")
      .call(yAxis)
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -margin.left)
      .attr("x", -height/2)
      .attr("dy", ".71em")
      .style("text-anchor", "middle")
      .text("% waiting processes");

  var line = d3.svg.line()
      .interpolate('linear')
      .defined(function(d) { return d.pcwaiting != null; })
      .x(function(d) { return x(d.tm); })
      .y(function(d) { return y(d.pcwaiting); });

  svg.append("path")
      .datum(data)
      .attr("class", "pcwaiting")
      .attr("d", line);

  svg.append("text")
          .attr("x", (width / 2))             
          .attr("y", 0 - (margin.top / 2))
          .attr("text-anchor", "middle")  
          .attr("class", "title")
          .text("Waiting process history");
  
  // now the median times
  target = "#process_wait_times";
  svg = make_plot_area(target, width, height, margin);

  // use the same x-axis
  svg.append("g")
      .attr("class", "axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)
      .append("text")
      .attr("x", width / 2 )
      .attr("y",  margin.bottom)
      .attr("dy", -5)
      .style("text-anchor", "middle")
      .text("Time");

  y.domain(d3.extent(data, function(d) { return d.medianwait; })).nice();
  svg.append("g")
      .attr("class", "axis")
      .call(yAxis)
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -margin.left)
      .attr("x", -height/2)
      .attr("dy", ".71em")
      .style("text-anchor", "middle")
      .text("Median wait time");

  line.y(function(d) { return y(d.medianwait); })
      .defined(function(d) { return d.medianwait != null; });
  svg.append("path")
      .datum(data)
      .attr("class", "medianwait")
      .attr("d", line);

 });
}

function make_plot_area(target, width, height, margin) {
  return d3.select(target).append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
}

