import os
import cherrypy
import hipchat
from flask import Flask, json, render_template, request

def build_app():
    app = Flask("Pipeline Notifier")
    app.debug = True
    current_reminder = None

    hipchat_token = os.environ["HIPCHAT_TOKEN"]
    hipchat_room = os.environ["HIPCHAT_ROOM"]

    @app.route("/", methods=["GET"])
    def show_set_reminder():
      print("show")
      return render_template("set-reminder.html")
      
    @app.route("/", methods=["POST"])
    def actually_set_reminder():
      global current_reminder
      print("set")
      current_reminder = request.form['reminder']
      return render_template("set-reminder.html")
      
    @app.route("/ping")
    def maybe_send_reminder():
      global current_reminder
      
      if current_reminder:
        hipchatConn = hipchat.HipChat(token=hipchat_token)
        hipchatConn.method(url='rooms/message', method='POST', parameters={
            'room_id': hipchat_room,
            'from': 'Daily Reminder',
            'message_format': 'html',
            'notify': False,
            'color': 'purple',
            'message': current_reminder
        })
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