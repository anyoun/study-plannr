$ ->
	timePickerClosed = (time, picker) ->
		console.log(picker.id + " set to " + time)
		start_time = $('#start-time-picker').val()
		end_time = $('#end-time-picker').val()
		console.log("Start: " + start_time + " End: " + end_time)
		url = '/schedule/' + scheduleKey + '/edit'
		post_data = { start_time: start_time, end_time: end_time }
		await $.post url, post_data, defer response_data, status, xhr
		console.log('Edit complete.')
		FullRerender response_data

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

	postAndRefresh = (event) ->
		event.preventDefault()
		await $.post event.target, "", defer response_data, status, xhr
		console.log 'Post and refresh' 
		FullRerender response_data

	FullRerender = (schedule) ->
		$("#schedule-container").html(ich.schedule(schedule))
		$(".item-more-link").click postAndRefresh
		$(".item-less-link").click postAndRefresh
		$(".item-remove-link").click postAndRefresh
		$("#add-subject-form").submit 

	FullRerender originalSchedule
	
	$("#check-enable-breaks").click ->
		url = '/schedule/' + scheduleKey + '/edit'
		checked = $("#check-enable-breaks").is(':checked')
		post_data = { enable_breaks: checked }
		await $.post url, post_data, defer response_data, status, xhr
		console.log "Changed enable-breaks"
		FullRerender response_data