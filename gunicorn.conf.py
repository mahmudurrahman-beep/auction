# gunicorn.conf.py
import multiprocessing

# Worker configuration
workers = 1  # Free tier limitation
worker_class = 'sync'
worker_connections = 1000
timeout = 30  # Increased timeout for AI requests
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'auction'
