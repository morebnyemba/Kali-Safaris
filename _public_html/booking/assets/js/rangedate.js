$from = $("#from");
$to = $("#to");
$range = $("#range");
$nights = $("#nbNights");

var array_dates = [];
var map_dates = [];

var dateFormat = "yy/mm/dd";
var range = 30;
initialise();

$range.on("change", function() {
  range = $range.val();
  $to.datepicker("option", "maxDate", getMaxDate($from.val(), range));
});
$from
  .datepicker({
    changeMonth: true,
    numberOfMonths: 1,
    minDate: 0
  })
  .on("change", function() {
    $to.datepicker("option", "minDate", $from.val());
    $to.datepicker("option", "maxDate", getMaxDate($from.val(), range));
  });

$to
  .datepicker({
    defaultDate: "+1w",
    changeMonth: true,
    numberOfMonths: 1
  })
  .on("change", function() {
    map_dates = [];
    setSelectedNights();
  });

function setDate(element) {
  var date;
  try {
    date = $.datepicker.parseDate(dateFormat, element.value);
  } catch (error) {
    date = null;
  }

  return date;
}

function getMaxDate(date, range) {
  var yyyy,
    mm,
    dd = 0;
  if (date.includes("-")) {
    var arr = date.split("-");
    console.log(arr);
    var dd = parseInt(arr[1]) + parseInt(range);
    var mm = parseInt(arr[0]) - 1;
    var yyyy = arr[2];
  } else if (date.includes("/")) {
    console.log(arr);
    var arr = date.split("/");
    var dd = parseInt(arr[1]) + parseInt(range);
    var mm = parseInt(arr[0]) - 1;
    var yyyy = arr[2];
  }
  return new Date(yyyy, mm, dd);
}
function initialise() {
  var start_date = getCurrentDate();
  var end_date = getNextWeek();
}

function parseDate(date) {
  if (date.includes("-")) {
    var arr = date.split("-");
    return arr[2] + "-" + arr[0] + "-" + arr[1];
  } else if (date.includes("/")) {
    var arr = date.split("/");
    return arr[2] + "-" + arr[0] + "-" + arr[1];
  } else {
    return null;
  }
}

function getCurrentDate() {
  var today = new Date();
  var dd = today.getDate();
  var mm = today.getMonth() + 1; //January is 0!
  var yyyy = today.getFullYear();

  if (dd < 10) {
    dd = "0" + dd;
  }

  if (mm < 10) {
    mm = "0" + mm;
  }

  return mm + "-" + dd + "-" + yyyy;
}
function getNextWeek() {
  var nextWeek = new Date();
  var dd = nextWeek.getDate() + 7;
  var mm = nextWeek.getMonth() + 1; //January is 0!
  var yyyy = nextWeek.getFullYear();

  if (dd < 10) {
    dd = "0" + dd;
  }

  if (mm < 10) {
    mm = "0" + mm;
  }

  return mm + "-" + dd + "-" + yyyy;
}

function setSelectedNights() {
  var diff = new Date(new Date($to.val()) - new Date($from.val()));
  $nights.text(diff / 1000 / 60 / 60 / 24);
}
