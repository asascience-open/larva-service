# Gunicorn configuration for production environment

bind = "127.0.0.1:4000"
workers = 2
debug = True
daemon = True
pidfile = "gunicorn.pid"
logfile = "gunicorn.log"