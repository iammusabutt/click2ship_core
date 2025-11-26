$(document).ready(function() {
    // $("#origin").select2({
    //        placeholder:'Select Origin'
    //    })
    //    $("#destination").select2({
    //        placeholder:'Select Destination'
    //    })
    //    $("#product").select2({
    //        placeholder:'Select Product',
    //    })
    $("#weight").numeric({ negative: false })

});

function getOrigin(e) {
    var value = $(e.target, 'option:selected').val();
    $.ajax({
            url: baseurl + 'getAirports',
            type: 'POST',
            // dataType: 'default: Intelligent Guess (Other values: xml, json, script, or html)',
            data: { code: value, type: 'origin' },
        })
        .done(function(res) {
            var re = JSON.parse(res)
            var airports = '<option value="" disabled selected>Airport</option>';
            if (re.length > 0) {
                $.each(re, function(index, val) {
                    airports += '<option value="' + val.code + '">' + val.name + '</option>'
                });
                $('#origin_airpot').html(airports)
            }
        })
        .fail(function() {
            console.log("error");
        })
        .always(function() {
            console.log("complete");
        });

}

function getDestination(e) {
    var value = $(e.target, 'option:selected').val();
    $.ajax({
            url: baseurl + 'getAirports',
            type: 'POST',
            // dataType: 'default: Intelligent Guess (Other values: xml, json, script, or html)',
            data: { code: value, type: 'dest' },
        })
        .done(function(res) {
            var re = JSON.parse(res)
            var airports = '<option value="" disabled selected>Airport</option>';
            if (re.length > 0) {
                $.each(re, function(index, val) {
                    airports += '<option value="' + val.code + '">' + val.name + '</option>'
                });
                $('#destination_airport').html(airports)
            }
        })
        .fail(function() {
            console.log("error");
        })
        .always(function() {
            console.log("complete");
        });

}

var path = window.location.pathname.split('/');
if (path[1] === 'trucking') {
    $("#type").on('change', function(e) {
        var value = $(this).val()
        var origin = $("#origin option:selected").val();
        $.ajax({
            type: "post",
            url: baseurl + "getTruckingLoc",
            data: { origin: origin, type: value },
            beforeSend: function() {
                $("#from").html('')
                $("#to").html('')
            },
            success: function(response) {
                var res = JSON.parse(response)
                console.log(res.from)
                if (res.from.length > 0) {
                    var fromOptions = '<option value="">Select</option>';
                    $.each(res.from, function(ind, val) {
                        fromOptions += '<option value="' + val.name + '">' + val.name + '</option>';
                    });

                    // Now you can do something with 'fromOptions', for example, append it to a select element
                    // Assuming you have a select element with an id 'fromSelect', you can do the following:
                    $('#from').html(fromOptions);
                }
                if (res.to.length > 0) {
                    var toOptions = '<option value="">Select</option>';
                    $.each(res.to, function(ind, val) {
                        toOptions += '<option value="' + val.name + '">' + val.name + '</option>';
                    });

                    // Now you can do something with 'toOptions', for example, append it to a select element
                    // Assuming you have a select element with an id 'toSelect', you can do the following:
                    $('#to').html(toOptions);
                }
            }
        });
    })
}

if (path[1] === 'sea') {
   $('#sorigin').on('change',function(){
    var value = $(this).val()
     var originPortSelect = $('#originport');
    $.ajax({
        url: baseurl  + 'web/getOriginPorts',
        type: 'POST',
        data: {country: value,type:'origin'},
        beforeSend:function(){
    originPortSelect.empty();

        }
    })
    .done(function(res) {
        var res = JSON.parse(res)
        if(res.length>0){
        // Assuming 'origin_port' is the ID of your select element
   

    // Clear existing options
    originPortSelect.empty();
    originPortSelect.append('<option value="" disabled selected>Select Origin Port</option>');
    // Add new options based on the JSON response
    $.each(res, function(index, option) {
        originPortSelect.append('<option value="' + option.origin_port + '">' + option.origin_port + '</option>');
    });
        }
    })
    
   })

   $("#originport").on('change',function(){

    var sorigin = $('#sorigin').val()
    var originport = $("#originport option:selected").val()
     var sdestination = $('#sdestination');
       $.ajax({
          url: baseurl  + 'web/getDestCountries',
        type: 'POST',
        data: {country:sorigin,port:originport},
        beforeSend:function(){
        sdestination.empty();
        }
       })
       .done(function(res) {
           var res = JSON.parse(res)
        if(res.length>0){
        sdestination.append('<option value="" disabled selected>Select Destination</option>');
        // Add new options based on the JSON response
        $.each(res, function(index, option) {
            sdestination.append('<option value="' + option.destination + '">' + option.destination+ '</option>');
        }); 
        }
       })
      
       
   })

   $('#sdestination').on('change',function(){
    var origin  = $("#sorigin option:selected").val();
    var origin_port  = $("#originport option:selected").val();
    var destination  = $("#sdestination option:selected").val();
    var sdestport = $("#sdestport")
    $.ajax({
        url: baseurl  + 'web/getDestPorts',
        type: 'POST',
        data: {
            origin :origin,
            origin_port :origin_port,
            destination :destination,

        },
        beforeSend:function(){
    sdestport.empty();

        }
    })
    .done(function(res) {
        var res = JSON.parse(res)
        if(res.length>0){
        sdestport.append('<option value="" disabled selected>Select Destination</option>');
        // Add new options based on the JSON response
        $.each(res, function(index, option) {
            sdestport.append('<option value="' + option.dest_port + '">' + option.dest_port+ '</option>');
        }); 
        
        }
    })
    
   })
}