$ ->
	$.ajaxSetup { type: 'POST', dataType: 'json' }

	$('#error-box').hide()

	showError = (message) ->
		console.log('Showing error: ' + message)
		$('#error-box-message').text(message)
		$('#error-box').show()

	$('#error-box').ajaxError (event, jqXHR, ajaxSettings, thrownError) ->
		showError('AJAX error: ' + thrownError)

	postScheduleEdit = (postData) ->
		url = '/schedule/' + scheduleKey + '/edit'
		await $.post url, postData, defer response_data, status, xhr
		console.log('Edit complete.')
		FullRerender response_data

	timePickerClosed = (time, picker) ->
		console.log(picker.id + " set to " + time)
		start_time = $('#start-time-picker').val()
		end_time = $('#end-time-picker').val()
		console.log("Start: " + start_time + " End: " + end_time)
		postScheduleEdit { start_time: start_time, end_time: end_time }

	options =
		showPeriod: true
		showLeadingZero: false
		showMinutesLeadingZero: false
		onClose: timePickerClosed
	$('#start-time-picker').timepicker options
	$('#end-time-picker').timepicker options

	$('#add-subject-form').submit (event) ->
		event.preventDefault()
		url = $('#add-subject-form').attr('action')
		post_data = { name: $('#add-item-name-textbox').val() }
		await $.post url, post_data, defer response_data, status, xhr
		console.log 'Post and refresh' 
		FullRerender response_data
		$('#add-item-name-textbox').val(null)

	$('#schedule-name-header').editable '/schedule/' + scheduleKey + '/edit', {
		tooltip: 'Click to change schedule name.'
		indicator: '<div class="schedule-name-loading-placeholder"><img src="/images/ajax-loader.gif"></div>'
		cssclass: 'schedule-name-header-editing'
		onblur: 'submit'
		name: 'name'
		width: 'none'
	}
	$('#break-time').editable ((value, settings) -> postScheduleEdit { break_time_minutes: value };return value), {
		tooltip: 'Click to change the length of breaks.'
		indicator: '<div class="schedule-name-loading-placeholder"><img src="/images/ajax-loader.gif"></div>'
		cssclass: 'break-time-editing'
		width: 'none'
	}

	postAndRefresh = (event) ->
		event.preventDefault()
		await $.post event.target, "", defer response_data, status, xhr
		console.log 'Post and refresh' 
		FullRerender response_data

	FullRerender = (schedule) ->
		$('#schedule-container').html(ich.schedule(schedule))
		$('.item-more-link').click postAndRefresh
		$('.item-less-link').click postAndRefresh
		$('.item-remove-link').click postAndRefresh
		$('#add-subject-form').submit('')
		$('.subject-name').each (i,subjectName) ->
			subjectName = $(subjectName)
			subjectName.editable '/schedule/' + scheduleKey + '/' + subjectName.attr('data-key') + '/rename', {
				tooltip	  : 'Click to change subject name.',
				indicator : '<div class="schedule-name-loading-placeholder"><img src="/images/ajax-loader.gif"></div>',
				cssclass  : 'subject-name-editing',
				onblur    : 'submit',
				width: 'none'
			}

		#Add current time
		#currentTime = new Date(2012, 2, 26, 12, 5, 0)
		currentTime = new Date()
		currentSeconds = currentTime.getHours() * 3600 + currentTime.getMinutes() * 60 + currentTime.getSeconds()
		if currentSeconds < schedule.end_time_sec and currentSeconds > schedule.start_time_sec
			totalSeconds = schedule.end_time_sec - schedule.start_time_sec
			percentage = (currentSeconds - schedule.start_time_sec) / totalSeconds * 100
			m = $("<div style=\"border-bottom: black 3px solid;position:relative;top:#{percentage}%;\"/>")
			$('#marker-container').children().remove()
			$('#marker-container').append(m)
			pad = (n) -> if n < 10 then "0#{n}" else "#{n}"
			formattedTime = pad(currentTime.getHours()) + ":" + pad(currentTime.getMinutes())
			m.append("<div style=\"float:left;\">#{formattedTime}</div>")
		

	FullRerender originalSchedule
	
	$("#check-enable-breaks").click ->
		url = '/schedule/' + scheduleKey + '/edit'
		checked = $("#check-enable-breaks").is(':checked')
		post_data = { enable_breaks: checked }
		await $.post url, post_data, defer response_data, status, xhr
		console.log "Changed enable-breaks"
		FullRerender response_data

	if window.webkitNotifications
		$('#check-enable-notifications').click ->
			if $('#check-enable-notifications').attr('checked')
				if window.webkitNotifications.checkPermission() != 0
					await window.webkitNotifications.requestPermission
				popup = window.webkitNotifications.createNotification("/images/logo.png", "title", "body");
				popup.show()
				window.setTimeout( ( -> popup.cancel() ), 1000 ) 