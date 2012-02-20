import cgi
import os
import logging
import re

import json

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app, login_required
from google.appengine.ext import db
from time import sleep
from datetime import time, datetime

class Schedule(db.Model):
    user = db.UserProperty()
    name = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    start_time = db.TimeProperty(default=time(9,0,0))
    end_time = db.TimeProperty(default=time(17,0,0))
    enable_breaks = db.BooleanProperty(default=False)
    break_time_sec = db.IntegerProperty(default=600)
    def get_NumSubjects(self):
        return self.scheduleitem_set.count()

class ScheduleItem(db.Model):
    schedule = db.ReferenceProperty(Schedule)
    name = db.StringProperty()
    time_weight = db.FloatProperty()
    ordinal = db.IntegerProperty()
     
TIME_FORMAT_STRING = '%I:%M %p'
ADD_FAKE_DELAYS = False

#COLOR_LIST = [ '#0F4FA8', '#FFCA00', '#FF6200' ]
COLOR_LIST = ['rgb(228,26,28)', 'rgb(55,126,184)', 'rgb(77,175,74)', 'rgb(152,78,163)', 'rgb(255,127,0)', 'rgb(255,255,51)', 'rgb(166,86,40)', 'rgb(247,129,191)', 'rgb(153,153,153)']
BREAK_COLOR = ['rgb(128,128,128)']
def get_color_for_item(scheduleItem):
    return COLOR_LIST[scheduleItem['ordinal'] % len(COLOR_LIST)]
def time_diff(x, y):
    return 3600*(x.hour-y.hour) + 60*(x.minute-y.minute) + x.second-y.second
def add_time(t, delta_seconds):
    total_seconds = time_diff(t, time(0)) + delta_seconds
    td_hours = total_seconds // 3600
    td_minutes = (total_seconds // 60) % 60
    td_seconds = total_seconds % 60
    logging.info("Seconds: %s", total_seconds)
    logging.info("%s %s %s", td_hours,td_minutes,td_seconds)
    return time(int(td_hours), int(td_minutes), int(td_seconds))
def multi_duration(td, factor):
    return td * factor
    #total = td.seconds + td.days * 24 * 3600
    #return timedelta(seconds = total * factor)
def round_time_15min(t):
    if t.minute > 53:
        return time(t.hour + 1, 0, 0)
    elif t.minute > 37:
        return time(t.hour, 30, 0)
    elif t.minute > 7:
        return time(t.hour, 15, 0)
    else:
        return time(t.hour, 0, 0)
def round_time_5min(t):
    if t.minute > 57:
        return time(t.hour + 1, 0, 0)
    else:
        return time(t.hour, t.minute // 5 * 5, 0)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif isinstance(obj, Schedule):
            return {
                'name': obj.name,
                'key': str(obj.key()),
                'date': obj.date,
                'start_time': obj.start_time,
                'end_time': obj.end_time,
            }
        return json.JSONEncoder.default(self, obj)

class HomePage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        has_user = user is not None
        template_values = {
            'is_loggedin' : has_user,
            'login_link' : users.create_login_url(self.request.uri),
            'logout_link' : users.create_logout_url(self.request.uri),
            'user_name' : user.nickname() if has_user else None,
        }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class SchedulesPage(webapp.RequestHandler):
    @login_required
    def get(self, format):
        user = users.get_current_user()
        schedules = Schedule.all()
        schedules.filter("user = ", user)
        if format == 'json':
            return_json(self, list(schedules.run()))
        else:
            template_values = {
                'schedules' : schedules,
                'logout_link' : users.create_logout_url(self.request.uri),
                'user_name' : user.nickname(),
            }        
            path = os.path.join(os.path.dirname(__file__), 'schedules.html')
            self.response.out.write(template.render(path, template_values))

def GetSchedule(schedule_key):
    user = users.get_current_user()
    if not user:
        return None
    schedule = Schedule.get(db.Key(schedule_key))
    if schedule.user != user:
        return None
    return schedule


def calculate_schedule_items(schedule):
    items = schedule.scheduleitem_set
    calc_items = []
    total_weight = sum(i.time_weight for i in items)
    start_time = schedule.start_time
    end_time = schedule.end_time
    total_duration = time_diff(end_time, start_time)
    current_time = start_time
    for (index, i) in enumerate(items):
        if index != 0 and schedule.enable_breaks:
            calc_items.append({
                'key' : '',
                'name' : 'Break',
                'ordinal': i.ordinal - 0.5,
                'pct': schedule.break_time_sec / total_duration,
                'start_time': current_time.strftime(TIME_FORMAT_STRING),
                'end_time': add_time(current_time, schedule.break_time_sec).strftime(TIME_FORMAT_STRING),
                'get_color': BREAK_COLOR,
            })

        ci = { }
        ci['key'] = str(i.key())
        ci['name'] = i.name
        ci['ordinal'] = i.ordinal
        ci['pct'] = 100.0 * i.time_weight / total_weight
        
        if schedule.enable_breaks and index != 0:
            item_start = add_time(current_time, -schedule.break_time_sec / 2)
        else:
            item_start = current_time
        ci['start_time'] = item_start.strftime(TIME_FORMAT_STRING)
        
        duration = multi_duration(total_duration, ci['pct']/100.0)
        current_time = round_time_5min(add_time(current_time, duration))

        if schedule.enable_breaks:
            item_end = add_time(current_time, schedule.break_time_sec / 2)
        else:
            item_end = current_time
        ci['end_time'] = item_end.strftime(TIME_FORMAT_STRING)

        ci['get_color'] = get_color_for_item(ci)
        calc_items.append(ci)
    if len(calc_items) > 0:
        calc_items[-1]['end_time'] = end_time.strftime(TIME_FORMAT_STRING)
    current_time = end_time
    return (calc_items, start_time, end_time)

def return_json(request_handler, obj):
    request_handler.response.headers['Content-Type'] = 'application/json'
    request_handler.response.out.write(json.dumps(obj, cls=DateTimeEncoder))
    
class ViewSchedule(webapp.RequestHandler):
    @login_required
    def get(self, schedule_key, format):
        schedule = GetSchedule(schedule_key)
        if schedule is None:
            self.redirect('/')
            return
        (calc_items, start_time, end_time) = calculate_schedule_items(schedule)
        has_user = users.get_current_user() is not None
        if format == 'json':
            return_json(self, calc_items)
        else:    
            template_values = {
                'schedule' : schedule,
                'items' : calc_items,
                'is_loggedin' : has_user,
                'login_link' : users.create_login_url(self.request.uri),
                'logout_link' : users.create_logout_url(self.request.uri),
                'user_name' : users.get_current_user().nickname() if has_user else None,
                'start_time' : start_time.strftime(TIME_FORMAT_STRING),
                'end_time' : end_time.strftime(TIME_FORMAT_STRING),
            }
            path = os.path.join(os.path.dirname(__file__), 'schedule.html')
            self.response.out.write(template.render(path, template_values))

class AddSchedule(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect('/')
            return            
        new_schedule = Schedule()
        new_schedule.user = user
        new_schedule.name = self.request.get('name')
        new_schedule.put()
        new_item = ScheduleItem()
        new_item.schedule = new_schedule
        new_item.name = 'Subject 1'
        new_item.time_weight = 1.0
        new_item.ordinal = 0
        new_item.put()
        self.redirect('/schedule/' + str(new_schedule.key()))

class AddScheduleItem(webapp.RequestHandler):
    def post(self, schedule_key):
        schedule = GetSchedule(schedule_key)
        if schedule is None:
            self.redirect('/')
            return
        last_item = schedule.scheduleitem_set.order('-ordinal').get()
        new_item = ScheduleItem()
        new_item.schedule = schedule
        new_item.name = self.request.get('name')
        new_item.time_weight = 1.0
        new_item.ordinal = 0 if last_item is None else last_item.ordinal + 1
        new_item.put()
        self.redirect('/schedule/' + str(schedule.key()))
        
class EditScheduleItem(webapp.RequestHandler):
    def post(self, schedule_key, item_key, action):
        item = ScheduleItem.get(db.Key(item_key))
        if item.schedule.user != users.get_current_user():
            self.redirect('/')
            return
        if ADD_FAKE_DELAYS:
            sleep(1)
        if action == 'more':
            item.time_weight *= 1.1
            item.put()
        elif action == 'less':
            item.time_weight *= .9
            item.put()
        elif action == 'remove':
            item.delete()
        elif action == 'rename':
            item.name = self.request.get("value")
            item.put()
            #For renames, just write out the new name rather than all items
            self.response.out.write(item.name)
            return
        else:
            raise Exception('Unknown mode')
        #Return all schedule items
        (calc_items, start_time, end_time) = calculate_schedule_items(item.schedule)
        return_json(self, calc_items)

class EditSchedule(webapp.RequestHandler):
    def parse_time(self, s):
        t = datetime.strptime(s, '%I:%M %p').time()
        #logging.info("String: '%s' time: '%s'" % (s,t))
        return t
    def valid(self, s):
        return s is not None and s != ''
    def post(self, schedule_key):
        schedule = GetSchedule(schedule_key)
        if schedule.user != users.get_current_user():
            self.redirect('/')
            return
        if ADD_FAKE_DELAYS:
            sleep(1)
        
        if self.valid(self.request.get("name")):
            schedule.name = self.request.get("name")
            schedule.put()
            self.response.out.write(schedule.name)
            return
        if self.valid(self.request.get("enable_breaks")):
            schedule.enable_breaks = self.request.get("enable_breaks").lower() in ["true", "on"]
        if self.valid(self.request.get("start_time")):
            schedule.start_time = self.parse_time(self.request.get("start_time"))            
        if self.valid(self.request.get("end_time")):
            schedule.end_time = self.parse_time(self.request.get("end_time"))
        
        schedule.put()
        (calc_items, start_time, end_time) = calculate_schedule_items(schedule)
        return_json(self, calc_items)
        
class RemoveSchedule(webapp.RequestHandler):
    def post(self, schedule_key):
        schedule = GetSchedule(schedule_key)
        if schedule.user != users.get_current_user():
            self.redirect('/')
            return
        schedule.delete()
        self.redirect('/')

        
application = webapp.WSGIApplication(
                                     [('/', HomePage),
                                      ('/schedules(json)?', SchedulesPage),
                                      ('/add_schedule', AddSchedule),
                                      ('/schedule/([^/]*)/add', AddScheduleItem),
                                      ('/schedule/([^/]*)/([^/]*)/(more|less|remove|rename)', EditScheduleItem),
                                      ('/schedule/([^/]*)/edit', EditSchedule),
                                      ('/schedule/([^/]*)/remove', RemoveSchedule),
                                      ('/schedule/([^/]*)/?(json)?', ViewSchedule)],
                                     debug=True)
