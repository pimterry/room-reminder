import os
import cherrypy
import hipchat
import redis
from datetime import datetime, timedelta
from flask import Flask, json, render_template, request

def build_app():
    app = Flask("Pipeline Notifier")
    app.debug = True

    hipchat_token = os.environ["HIPCHAT_TOKEN"]
    hipchat_room = os.environ["HIPCHAT_ROOM"]

    redis_url = os.environ["REDISTOGO_URL"]
    redis_conn = redis.from_url(redis_url)

    # Set to 8am initially, so we end up pinging at around 8am every day.
    eight_am_today_utc = datetime.utcnow().replace(hour=8, minute=0, second=0, microsecond=0)
    redis_conn.set('last_reminder_time', eight_am_today_utc)

    @app.route("/", methods=["GET"])
    def show_set_reminder():
      return render_template("set-reminder.html")

    @app.route("/", methods=["POST"])
    def actually_set_reminder():
      current_reminder = request.form['reminder']
      redis_conn.set('reminder', current_reminder)
      return render_template("set-reminder.html")
      
    @app.route("/ping")
    def maybe_send_reminder():
      try:
        last_reminder_time = datetime.strptime(redis_conn.get('last_reminder_time').decode("UTF-8"), "%Y-%m-%d %H:%M:%S")
        current_reminder = redis_conn.get('reminder')
      except Exception as e:
        print("Failed to get time and reminder from Redis: %s" % (e,))
        current_reminder = None
        last_reminder_time = None

      if (current_reminder and
          last_reminder_time + timedelta(days=1) <= datetime.utcnow()):     
        hipchatConn = hipchat.HipChat(token=hipchat_token)
        hipchatConn.method(url='rooms/message', method='POST', parameters={
            'room_id': hipchat_room,
            'from': 'Daily Reminder',
            'message_format': 'html',
            'notify': False,
            'color': 'purple',
            'message': current_reminder
        })

        redis_conn.set('last_reminder_time', datetime.utcnow())        
        return "sent"

      return "no reminder set"
    
    return app

def run_server(app):
    cherrypy.tree.graft(app, '/')

    cherrypy.config.update({
        'engine.autoreload_on': True,
        'log.screen': True,
        'server.socket_port': int(os.environ.get('PORT', '8081')),
        'server.socket_host': '0.0.0.0'
    })

    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == '__main__':
    app = build_app()
    run_server(app)