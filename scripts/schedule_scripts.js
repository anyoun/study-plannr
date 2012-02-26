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

    var showError = function(message){
    	console.log('Showing error: ' + message);
    	$('#error-box-message').text(message);
    	$('#error-box').show();
    };

    $('#error-box').ajaxError(function(event, jqXHR, ajaxSettings, thrownError){
    	showError('AJAX error: ' + thrownError);
    });
    
	$('.subject-name').each(function(i,subjectName) {
		subjectName = $(subjectName);
		var itemKey = subjectName.attr('data-key');
		subjectName.editable('/schedule/' + scheduleKey + '/' + itemKey + '/rename', {
			tooltip	  : 'Click to change subject name.',
	 		indicator : '<div class="schedule-name-loading-placeholder"><img src="/images/ajax-loader.gif"></div>',
	 		cssclass  : 'subject-name-editing',
	 		onblur    : 'submit',
		});
	});
	
	$('.schedule-name').editable('/schedule/' + scheduleKey + '/edit', {
		tooltip	  : 'Click to change schedule name.',
 		indicator : '<div class="schedule-name-loading-placeholder"><img src="/images/ajax-loader.gif"></div>',
 		cssclass  : 'schedule-name-editing',
 		onblur    : 'submit',
		name	  : 'name',
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
});