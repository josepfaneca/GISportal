function createGraph(graphOptions) {
   $(document.body).append(
      '<div id="' + graphOptions.id + '-graph" class="unselectable" title="' + graphOptions.title + '">' +
         '<div class="graph"></div>' +
      '</div>'
   );
   
   $('#' + graphOptions.id + '-graph').dialog({
      position: ['center', 'center'],
      width: 700,
      height: 450,
      resizable: false,
      autoOpen: true,
      close: function() {
         $('#' + graphOptions.id + '-graph').remove();
      }
   }).dialogExtend({
      "help": false,
      "minimize": true,
      "dblclick": "collapse",
   });

   $('#' + graphOptions.id + '-graph').children('.graph').width(600).height(384);
   
   var 
      container = $('#' + graphOptions.id + '-graph').children('.graph').get(0), 
      start, graph;
   
   graph = drawGraph(container, graphOptions.data, graphOptions.options);
   
   if(graphOptions.draggable && graphOptions.draggable == true) {
      Flotr.EventAdapter.observe(graph.overlay, 'mousedown', initDrag);
   }
   
   if(graphOptions.selectable && graphOptions.selectable == true) {
      Flotr.EventAdapter.observe(container, 'flotr:select', function(area) {
         // Draw selected area
         graph = drawGraph(container, graphOptions.data, {
            xaxis : { min : area.x1, max : area.x2, mode : 'time', labelsAngle : 45 },
            yaxis : { min : area.y1, max : area.y2 }
         });
      });
           
      // When graph is clicked, draw the graph with default area.
      Flotr.EventAdapter.observe(container, 'flotr:click', function () { graph = drawGraph(container, graphOptions.data); });
   }
   
   function drawGraph(container, data, opts)
   {
      var optionsClone = Flotr._.extend(Flotr._.clone(graphOptions.options), opts || {});
      
      return Flotr.draw(container, data, optionsClone);
   }
   
   function initDrag(e) {
      start = graph.getEventPosition(e);
      
      Flotr.EventAdapter.observe(document, 'mouseup', stopDrag);
      
      Flotr.EventAdapter.observe(document, 'mousemove', move);
   }
   
   function move(e) {
      var
         end = graph.getEventPosition(e),
         xaxis = graph.axes.x,
         offset = start.x - end.x;
         
      graph = drawGraph(container, graphOptions.data, {
         xaxis: {
            min: xaxis.min + offset,
            max: xaxis.max + offset
         }
      });
      
      Flotr.EventAdapter.observe(graph.overlay, 'mousedown', initDrag);
   }
   
   function stopDrag() {
      Flotr.EventAdapter.stopObserving(document, 'mousemove', move);
   }
   
      // function animate(t) {
      // data = [];
      // offset = 2 * Math.PI * (t - start) / 10000;
//       
      // // Sample the sane function
      // for(i = 0; i < 4 * Math.PI; i += 0.2) {
         // data.push([i, Math.sin(i - offset)]);
      // }
//       
      // graph = Flotr.draw(container, [ data ], { 
         // yaxis: {
            // max: 2,
            // min: -2
         // }
      // });
//       
//       
      // // Animate
      // setTimeout(function () { 
         // animate((new Date).getTime());
      // }, 50);
   // }
   
   //console.log("created graph and function");
   
   //animate(start);
   
   //console.log("animate");
}

function generateLineData()
{
   var d1 = [], d2 = [], d3 = [];
   
   // Create Sample Data
   for(var i = -60; i < 60; i += 0.5) {
      d1.push([i, Math.sin(i)+3*Math.cos(i)]);
      d2.push([i, Math.pow(1.1, i)]);
      d3.push([i, i + Math.random()*10]);
   }
   
   return [d1, d2,
      {
         data: d3,
         lines: { show: true },
         points: { show: true }
      }];
}

function generateCandleData()
{
   var d1 = [], price = 3.206, a, b, c;
   
   for (var i = -50; i < 50; i++) {
      a = Math.random();
      b = Math.random();
      c = (Math.random() * (a + b)) - b;
      d1.push([i, price, price + a, price - b, price + c]);
      price = price + c;
   }
   
   return [d1];
}

function generateBasicTimeData()
{
   var 
      d1 = [], 
      x, 
      start = new Date("2009/01/01 01:00").getTime();
   
   for (var i = 0; i < 100; i++) {
      x = start+(i*1000*3600*24*36.5);
      d1.push([x, i+Math.random()*30+Math.sin(i/20+Math.random()*2)*20+Math.sin(i/10+Math.random())*10]);
   }
   
   return [d1];
}

function lineOptions()
{
   return {
      xaxis: { min: 0, max: 20 },
      yaxis: { min: -10, max: 60 },
      title: 'Example Graph',
      mouse : {
        track           : true, // Enable mouse tracking
        lineColor       : 'purple',
        relative        : true,
        position        : 'ne',
        sensibility     : 1,
        trackDecimals   : 2,
        trackFormatter  : function (o) { return 'x = ' + o.x +', y = ' + o.y; }
      },
   };
}

function barOptions()
{
   return {
      bars: {
         show: true,
         horizontal: false,
         shadowsize: 0,
         barwidth: 25
      },
      title: 'Example Graph',
      yaxis: {
         min: 0,
         autoscaleMargin: 1
      }
   };
}

function candleOptions()
{
   return {
      candles: { show: true, candleWidth: 0.6 },
      xaxis: { noTicks: 10 },
      title: 'Example Graph'
   };
}

function basicTimeOptions()
{
   return {
      xaxis: {
         mode: 'time',
         labelsAngle: 45
      },
      selection: {
         mode: 'x'
      },
      HtmlText: false,
      title: 'Time'
   };
}