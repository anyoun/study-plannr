$ ->
	FullRerender = (schedule) ->
		#template = $("#")
		#view = { test: "hello world" }
		#partials = null
		#$("#schedule-container").html($.mustache(template, view, partials))
		end_time = schedule[schedule.length - 1].end_time
		$("#schedule-container").html(ich.schedule({ items: schedule, scheduleKey: scheduleKey, end_time:end_time }))

	$("#check-enable-breaks").click ->
		url = '/schedule/' + scheduleKey + '/edit'
		checked = $("#check-enable-breaks").is(':checked')
		post_data = { enable_breaks: checked }
		await $.post url, post_data, defer response_data, status, xhr
		console.log "Changed enable-breaks"
		#rerender response_data
		FullRerender response_data