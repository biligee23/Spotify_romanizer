"""
Gunicorn configuration file for production.
"""

# Number of worker processes
workers = 4  # A common starting point is (2 * number_of_cores) + 1

# The socket to bind to
bind = "0.0.0.0:5000"

# The type of worker process
# Use 'eventlet' for applications with long-running requests or async tasks
worker_class = "eventlet"

# Logging
accesslog = "-"  # Log access logs to stdout
errorlog = "-"   # Log error logs to stdout
loglevel = "info"