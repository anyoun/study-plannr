// Generated by IcedCoffeeScript 1.2.0p
(function() {
  var __slice = [].slice;

  window.iced = {
    Deferrals: (function() {

      function _Class(_arg) {
        this.continuation = _arg;
        this.count = 1;
        this.ret = null;
      }

      _Class.prototype._fulfill = function() {
        if (!--this.count) return this.continuation(this.ret);
      };

      _Class.prototype.defer = function(defer_params) {
        var _this = this;
        ++this.count;
        return function() {
          var inner_params, _ref;
          inner_params = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
          if (defer_params != null) {
            if ((_ref = defer_params.assign_fn) != null) {
              _ref.apply(null, inner_params);
            }
          }
          return _this._fulfill();
        };
      };

      return _Class;

    })(),
    findDeferral: function() {
      return null;
    }
  };
  window.__iced_k = function() {};

  $(function() {
    var FullRerender, options, postAndRefresh, postScheduleEdit, showError, timePickerClosed;
    $.ajaxSetup({
      type: 'POST',
      dataType: 'json'
    });
    $('#error-box').hide();
    showError = function(message) {
      console.log('Showing error: ' + message);
      $('#error-box-message').text(message);
      return $('#error-box').show();
    };
    $('#error-box').ajaxError(function(event, jqXHR, ajaxSettings, thrownError) {
      return showError('AJAX error: ' + thrownError);
    });
    postScheduleEdit = function(postData) {
      var response_data, status, url, xhr, ___iced_passed_deferral, __iced_deferrals,
        _this = this;
      ___iced_passed_deferral = iced.findDeferral(arguments);
      url = '/schedule/' + scheduleKey + '/edit';
      (function(__iced_k) {
        __iced_deferrals = new iced.Deferrals(__iced_k, {
          parent: ___iced_passed_deferral,
          filename: "/Users/will/Dropbox/medderschedule/scripts/schedule_scripts.iced",
          funcname: "postScheduleEdit"
        });
        $.post(url, postData, __iced_deferrals.defer({
          assign_fn: (function() {
            return function() {
              response_data = arguments[0];
              status = arguments[1];
              return xhr = arguments[2];
            };
          })(),
          lineno: 16
        }));
        __iced_deferrals._fulfill();
      })(function() {
        console.log('Edit complete.');
        return FullRerender(response_data);
      });
    };
    timePickerClosed = function(time, picker) {
      var end_time, start_time;
      console.log(picker.id + " set to " + time);
      start_time = $('#start-time-picker').val();
      end_time = $('#end-time-picker').val();
      console.log("Start: " + start_time + " End: " + end_time);
      return postScheduleEdit({
        start_time: start_time,
        end_time: end_time
      });
    };
    options = {
      showPeriod: true,
      showLeadingZero: false,
      showMinutesLeadingZero: false,
      onClose: timePickerClosed
    };
    $('#start-time-picker').timepicker(options);
    $('#end-time-picker').timepicker(options);
    $('#add-subject-form').submit(function(event) {
      var post_data, response_data, status, url, xhr, ___iced_passed_deferral, __iced_deferrals,
        _this = this;
      ___iced_passed_deferral = iced.findDeferral(arguments);
      event.preventDefault();
      url = $('#add-subject-form').attr('action');
      post_data = {
        name: $('#add-item-name-textbox').val()
      };
      (function(__iced_k) {
        __iced_deferrals = new iced.Deferrals(__iced_k, {
          parent: ___iced_passed_deferral,
          filename: "/Users/will/Dropbox/medderschedule/scripts/schedule_scripts.iced"
        });
        $.post(url, post_data, __iced_deferrals.defer({
          assign_fn: (function() {
            return function() {
              response_data = arguments[0];
              status = arguments[1];
              return xhr = arguments[2];
            };
          })(),
          lineno: 39
        }));
        __iced_deferrals._fulfill();
      })(function() {
        console.log('Post and refresh');
        FullRerender(response_data);
        return $('#add-item-name-textbox').val(null);
      });
    });
    $('#schedule-name-header').editable('/schedule/' + scheduleKey + '/edit', {
      tooltip: 'Click to change schedule name.',
      indicator: '<div class="schedule-name-loading-placeholder"><img src="/images/ajax-loader.gif"></div>',
      cssclass: 'schedule-name-header-editing',
      onblur: 'submit',
      name: 'name',
      width: 'none'
    });
    $('#break-time').editable((function(value, settings) {
      postScheduleEdit({
        break_time_minutes: value
      });
      return value;
    }), {
      tooltip: 'Click to change the length of breaks.',
      indicator: '<div class="schedule-name-loading-placeholder"><img src="/images/ajax-loader.gif"></div>',
      cssclass: 'break-time-editing',
      width: 'none'
    });
    postAndRefresh = function(event) {
      var response_data, status, xhr, ___iced_passed_deferral, __iced_deferrals,
        _this = this;
      ___iced_passed_deferral = iced.findDeferral(arguments);
      event.preventDefault();
      (function(__iced_k) {
        __iced_deferrals = new iced.Deferrals(__iced_k, {
          parent: ___iced_passed_deferral,
          filename: "/Users/will/Dropbox/medderschedule/scripts/schedule_scripts.iced",
          funcname: "postAndRefresh"
        });
        $.post(event.target, "", __iced_deferrals.defer({
          assign_fn: (function() {
            return function() {
              response_data = arguments[0];
              status = arguments[1];
              return xhr = arguments[2];
            };
          })(),
          lineno: 61
        }));
        __iced_deferrals._fulfill();
      })(function() {
        console.log('Post and refresh');
        return FullRerender(response_data);
      });
    };
    FullRerender = function(schedule) {
      var currentSeconds, currentTime, formattedTime, m, pad, percentage, totalSeconds;
      $('#schedule-container').html(ich.schedule(schedule));
      $('.item-more-link').click(postAndRefresh);
      $('.item-less-link').click(postAndRefresh);
      $('.item-remove-link').click(postAndRefresh);
      $('#add-subject-form').submit('');
      $('.subject-name').each(function(i, subjectName) {
        subjectName = $(subjectName);
        return subjectName.editable('/schedule/' + scheduleKey + '/' + subjectName.attr('data-key') + '/rename', {
          tooltip: 'Click to change subject name.',
          indicator: '<div class="schedule-name-loading-placeholder"><img src="/images/ajax-loader.gif"></div>',
          cssclass: 'subject-name-editing',
          onblur: 'submit',
          width: 'none'
        });
      });
      currentTime = new Date();
      currentSeconds = currentTime.getHours() * 3600 + currentTime.getMinutes() * 60 + currentTime.getSeconds();
      if (currentSeconds < schedule.end_time_sec && currentSeconds > schedule.start_time_sec) {
        totalSeconds = schedule.end_time_sec - schedule.start_time_sec;
        percentage = (currentSeconds - schedule.start_time_sec) / totalSeconds * 100;
        m = $("<div style=\"border-bottom: black 3px solid;position:relative;top:" + percentage + "%;\"/>");
        $('#marker-container').children().remove();
        $('#marker-container').append(m);
        pad = function(n) {
          if (n < 10) {
            return "0" + n;
          } else {
            return "" + n;
          }
        };
        formattedTime = pad(currentTime.getHours()) + ":" + pad(currentTime.getMinutes());
        return m.append("<div style=\"float:left;\">" + formattedTime + "</div>");
      }
    };
    FullRerender(originalSchedule);
    $("#check-enable-breaks").click(function() {
      var checked, post_data, response_data, status, url, xhr, ___iced_passed_deferral, __iced_deferrals,
        _this = this;
      ___iced_passed_deferral = iced.findDeferral(arguments);
      url = '/schedule/' + scheduleKey + '/edit';
      checked = $("#check-enable-breaks").is(':checked');
      post_data = {
        enable_breaks: checked
      };
      (function(__iced_k) {
        __iced_deferrals = new iced.Deferrals(__iced_k, {
          parent: ___iced_passed_deferral,
          filename: "/Users/will/Dropbox/medderschedule/scripts/schedule_scripts.iced"
        });
        $.post(url, post_data, __iced_deferrals.defer({
          assign_fn: (function() {
            return function() {
              response_data = arguments[0];
              status = arguments[1];
              return xhr = arguments[2];
            };
          })(),
          lineno: 102
        }));
        __iced_deferrals._fulfill();
      })(function() {
        console.log("Changed enable-breaks");
        return FullRerender(response_data);
      });
    });
    if (window.webkitNotifications) {
      return $('#check-enable-notifications').click(function() {
        var popup, ___iced_passed_deferral, __iced_deferrals,
          _this = this;
        ___iced_passed_deferral = iced.findDeferral(arguments);
        if ($('#check-enable-notifications').attr('checked')) {
          (function(__iced_k) {
            if (window.webkitNotifications.checkPermission() !== 0) {
              (function(__iced_k) {
                __iced_deferrals = new iced.Deferrals(__iced_k, {
                  parent: ___iced_passed_deferral,
                  filename: "/Users/will/Dropbox/medderschedule/scripts/schedule_scripts.iced"
                });
                window.webkitNotifications.requestPermission;
                __iced_deferrals._fulfill();
              })(__iced_k);
            } else {
              return __iced_k();
            }
          })(function() {
            popup = window.webkitNotifications.createNotification("/images/logo.png", "title", "body");
            popup.show();
            return __iced_k(window.setTimeout((function() {
              return popup.cancel();
            }), 1000));
          });
        } else {
          return __iced_k();
        }
      });
    }
  });

}).call(this);
