Dashing.gridsterLayout('[{"col":2,"row":1},{"col":1,"row":1},{"col":3,"row":1},{"col":2,"row":2},{"col":3,"row":2},{"col":1,"row":2},{"col":5,"row":1},{"col":4,"row":2},{"col":2,"row":3}]');
Dashing.widget_base_dimensions = [370, 340];
Dashing.numColumns = 5;
Batman.config.viewPrefix = window.location.pathname + '/views/';

var UNKNOWN_COLOR = "rgb(236, 102, 60)";
var OK_COLOR = "green";
var ERROR_COLOR = "red";


Dashing.on("ready", function() {

  function updateWidget(region, data) {
    if (Dashing.widgets[region] && Dashing.widgets[region].length > 0) {
      //console.log("* Update widget", region);
      Dashing.widgets[region][0].receiveData(data);
      Dashing.widgets[region][0].node.style.backgroundColor = data.backgroundColor;
    }
  }

  function updateAllSystems() {
    console.log("Updating all systems");
    var allRegions = [];

    var updateOne = function(region) {
      var req = $.ajax({
        url: "status",
        data: {region: region},
        dataType: "json"
      });

      if (region in CriticalRegions) {
        allRegions.push(req);
      }

      req.done(function(data) {
        updateWidget(region, data);
      });

      req.fail(function(xhr) {
        try {
          var data = JSON.parse(xhr.responseText);
          data.title = region;
          updateWidget(region, data);
        } catch (e) {
          updateWidget(region, {
            title: "ERROR!!",
            backgroundColor: ERROR_COLOR,
            updatedAt: (new Date()).getTime() / 1000
          });
          console.log(e);
        }
      });
    };

    for (var i = 0; i < Regions.length; i++) {
      updateOne(Regions[i]);
    }

    var critical = $.when.apply($, allRegions);
    critical.then(
      function() {
        updateWidget("overall", {text: "OK", backgroundColor: OK_COLOR});
        console.log("critical done");
      },
      function () {
        updateWidget("overall", {text: "Down", backgroundColor: ERROR_COLOR});
        console.log("critical fail");
      }
    );
  }

  updateAllSystems();
  setInterval(updateAllSystems, 60000);
});
