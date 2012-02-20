$ ->
	$("#check-enable-breaks").click ->
		url = '/schedule/' + scheduleKey + '/edit'
		checked = $("#check-enable-breaks").is(':checked')
		post_data = { enable_breaks: checked }
		await $.post url, post_data, defer response_data, status, xhr
		console.log "Changed enable-breaks"
		rerender response_data
     