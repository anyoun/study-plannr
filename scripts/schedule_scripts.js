var asyncGetScheduleItems = function(callback){
    $.ajax({
        url: '/schedule/' + scheduleKey + '/json',
        type: 'GET',
        success: function(data, status, xhr){
            console.log('Got schedule items JSON.');
			callback(data);
        },
    });
};
var rerender = function(items){
	console.log('rerender...');
	if(items == null) {
		console.log('rerender called with null items.')
		return;
	}
	for (var i=0; i < items.length; i++) {
		$('#item-row-' + items[i].key).css('height', items[i].pct + '%');
		$('#item-start-time-' + items[i].key).text(items[i].start_time);
	};
	var lastItem = items[items.length-1];
	$('#items-end-time').text(lastItem.end_time);
};

$(document).ready(function() {
    $.ajaxSetup({
        type: 'POST',
        dataType: 'json',
    });

    $('#error-box').hide();
    $('#error-box').ajaxError(function(event, jqXHR, ajaxSettings, thrownError){
    	console.log('AJAX error: ' + thrownError)
    	$(this).text('AJAX error: ' + thrownError)
    	$(this).show();
    });
    
	$('.subject-name').each(function(i,subjectName) {
		subjectName = $(subjectName);
		var itemKey = subjectName.attr('data-key');
		subjectName.editable('/schedule/' + scheduleKey + '/' + itemKey + '/rename', {
			tooltip	  : 'Click to change subject name.',
	 		indicator : '<div class="schedule-name-loading-placeholder"><img src="/images/ajax-loader.gif"></div>',
	 		cssclass  : 'subject-name-editing',
	 		onblur    : 'submit',
//			name	  : 'name',
		});
	});
	
	$('.schedule-name').editable('/schedule/' + scheduleKey + '/edit', {
		tooltip	  : 'Click to change schedule name.',
 		indicator : '<div class="schedule-name-loading-placeholder"><img src="/images/ajax-loader.gif"></div>',
 		cssclass  : 'schedule-name-editing',
 		onblur    : 'submit',
		name	  : 'name',
	});
	
	var ajaxAndRefresh = function(event){
		event.preventDefault();
		$.ajax({
			url: event.target,
			success: function(data, status, xhr){
                console.log('Called more/less link');
				rerender(data);
            },
		});
	};
	$(".item-more-link").click(ajaxAndRefresh);
	$(".item-less-link").click(ajaxAndRefresh);
	
	$(".item-remove-link").click(function(event){
		event.preventDefault();
		var uri = event.target.href;
		var anchor = $(this);
		$.ajax({
			url: uri,
			success: function(data, status, xhr){
                console.log('Called remove link');
				anchor.parents('.item-row').remove();
				rerender(data);
            },
		});
	});
	
	if( window.webkitNotifications ) {
		$('#check-enable-notifications').click(function(){
			if($('#check-enable-notifications').attr('checked')) {
				var gotPermissionsCallback = function() {
					var popup = window.webkitNotifications.createNotification("/images/logo.png", "title", "body");
					popup.show();
					window.setTimeout(function() { popup.cancel(); }, 1000 );
				}
				if( window.webkitNotifications.checkPermission() != 0 ) {
					window.webkitNotifications.requestPermission(gotPermissionsCallback);
				} else {
					gotPermissionsCallback();
				}
			}
		});
	}
	
	var timePickerClosed = function(time, picker){
		console.log(picker.id + " set to " + time);
		var start_time = $('#start-time-picker').val();
		var end_time = $('#end-time-picker').val()
		console.log("Start: " + start_time + " End: " + end_time)
		$.ajax({
			url: '/schedule/' + scheduleKey + '/edit',
			data: { start_time: start_time, end_time: end_time },
			processData: true,
			success: function(data, status, xhr){
				console.log('Edit complete.');
				rerender(data);
			},
		});
	};
	var options = {
		showPeriod: true,
		showLeadingZero: false,
		showMinutesLeadingZero: false,
		onClose: timePickerClosed,
	};
	$('#start-time-picker').timepicker(options);
	$('#end-time-picker').timepicker(options);
});