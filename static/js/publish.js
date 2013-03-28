(function () {
	var csrftoken = $.cookie('csrftoken');
	function csrfSafeMethod(method) {
	    // these HTTP methods do not require CSRF protection
	    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
	}
	function sameOrigin(url) {
	    // test that a given url is a same-origin URL
	    // url could be relative or scheme relative or absolute
	    var host = document.location.host; // host + port
	    var protocol = document.location.protocol;
	    var sr_origin = '//' + host;
	    var origin = protocol + sr_origin;
	    // Allow absolute or scheme relative URLs to same origin
	    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
	        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
	        // or any other URL that isn't scheme relative or absolute i.e relative.
	        !(/^(\/\/|http:|https:).*/.test(url));
	}
	$.ajaxSetup({
	    beforeSend: function(xhr, settings) {
	        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
	            // Send the token to same-origin, relative URLs only.
	            // Send the token only if the method warrants CSRF protection
	            // Using the CSRFToken value acquired earlier
	            xhr.setRequestHeader("X-CSRFToken", csrftoken);
	        }
	    }
	});
})();

$(document).ready(function() {
	var toggle_button = function(data, b) {
		var status, text;

		if (b.hasClass('btn-danger')) {
			text = 'Publish';
			$(b).data('published','False');
		} else {
			text = 'Unpublish';
			$(b).data('published','True');
		}

		b.toggleClass('btn-info')
			.toggleClass('btn-danger')
			.text(text);
	};

	var toggle_class_status = function() {
		var id = $(this).data('submission'),
			status = $(this).data('published'),
			div = $(this);
		$.post(caesar.urls.publish_code, {submission_id: id, published: status}, function(data) { toggle_button(data, div); });
	};

	$('.btn.publish').click(toggle_class_status);
});