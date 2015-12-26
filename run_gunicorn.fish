#!/usr/bin/env fish

# Configure environment
sed -nE 's/^([^=]+)=(.*)/set -x \1 \2/p' $PACTF_ROOT/.env | source -
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
