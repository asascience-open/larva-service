# Gunicorn configuration for production environment

bind = "127.0.0.1:8000"
workers = 2
debug = True
daemon = False
pidfile = "gunicorn.pid"
logfile = "gunicorn.log"
backlog = 2048