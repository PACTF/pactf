#!/usr/bin/env fish

# TODO(Yatharth): Port to bash

# Configure directories
set -l PACTF_ROOT (cd (dirname (status -f)); and pwd)
set -l PACTF_DJANGO_DIR "$PACTF_ROOT/django"
set -l PACTF_DJANGO_SETTINGS_MODULE pactf_web.settings
set -l PACTF_DJANGO_WSGI_MODULE pactf_web.wsgi
set -l PACTF_NAME pactf_web

sed -nE 's/^([^=]+)=(.*)/set -x \1 \2/p' $PACTF_ROOT/.env | source -
or exit 1
set -x PYTHONPATH "$PACTF_DJANGO_DIR" $PYTHONPATH

echo "Starting $PACTF_NAME from user "(whoami)

# Create the run directory if it doesn't exist
set -l RUNDIR (dirname "$PACTF_SOCKFILE")
if test ! -e "$RUNDIR"
    mkdir -p "$RUNDIR"
end

# Determine whether to use sockfile or serve directly
set -l bind_bit
if test "$PACTF_USE_SOCKFILE" -gt 0
    set bind_bit "unix:$PACTF_SOCKFILE"
else
    set bind_bit "$PACTF_URL"
end

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
eval "exec \"$PACTF_GUNICORN\" \"$PACTF_DJANGO_WSGI_MODULE:application\" \
  --name \"$PACTF_NAME\" \
  --workers \"$PACTF_NUM_WORKERS\" \
  --user=\"$PACTF_USER\" --group=\"$PACTF_GROUP\" \
  --log-level=debug \
  --bind=\"$bind_bit\" \
  --log-file=-"
