$(function() {
    // Error Code
    var invalid_account = 1;
    var invalid_feed = 2;

    function clear_error() {
        var error_message_field = $("#bot_error_message ul")[0];
        error_message_field.innerHTML = "";
    }

    function show_error(error) {
        var error_message_field = $("#bot_error_message ul")[0];
        $("#loading_img").css('display', 'none');
        for(var i = 0; i<error.length; ++i) {
            error_message_field.innerHTML += "<li>"+error[i]+"</li>";
        }
        return;
    }

    $("#edit_button").click(function() {
        // validate and process form here
        clear_error();
        $("#loading_img").css('display', 'inline');
        $("#submit_button").disabled = true;
        var errors = [];

        var key = $("#bot_key").val();

        var name = $("#bot_name").val();
        var password = $("#bot_password").val();
        var feed = $("#bot_feed").val();
        var message = $("#bot_message").val();
        var exkeywords = $("#bot_exkeywords").val();
        var interval = $("#bot_interval").val();
        var desc = $("#bot_desc").val();
        var enable = $("#bot_enable")[0].checked ? 1 : 0;

        dataString = "key=" + key;
        dataString += "&name=" + name;
        dataString += "&password=" + password;
        dataString += "&feed=" + feed;
        dataString += "&message=" + encodeURIComponent(message);
        dataString += "&exkeywords=" + exkeywords;
        dataString += "&interval=" + interval;
        dataString += "&desc=" + desc;
        dataString += "&enable=" + enable;

        if (feed.length < 5) {
            errors.push("feed URL is required");
        }
        if (password.length < 1) {
            errors.push("password is required");
        }
        if (name.length < 1) {
            errors.push("name is required");
        }
        if (errors.length > 0) {
            show_error(errors);
            alert(errors[0]);
            return false;
        }

        $.ajax({
            type: "POST",
            url: "/edit/",
            data: dataString,

            success: function(message) {
                if (message.length != 1) {
                    return;
                }

                var status = message[0] | 0;
                var errors = [];
                if (status & invalid_account) {
                    errors.push('Could not login the account');
                }
                if (status & invalid_feed) {
                    errors.push('Could not fetch the feed');
                }

                if (status == 0) {
                    $('#update_bot').html("<div id='message'></div>");
                    $('#message').html("<h2>Bot Updated! </h2>")
                    .append("<p><a href='/show/'>Configure your bots in detal.</a></p>")
                    .hide()
                    .fadeIn(1500, function() {
                        $('#message').append("<img id='checkmark' src='/img/check.png' />");
                    });
                } else {
                    show_error(errors);
                }
            }
        });
        return false;
    });
});