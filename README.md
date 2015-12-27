# PACTF (Alpha)

## Installation

- Activate a virtual environment with Python 3.5+
- `pip install -r requirements.txt`
- Create pactf_web/local_settings.py and .env
- `manage.py prep`
- Directly run using `run_gunicorn.fish` (TODO(Yatharth): support bash)
- (Optional:) Configure, validate and restart nginx to reverse proxy gunicorn via a sockfile
- (Optional:) Install and configure supervior to keep gunicorn running (reread, update)


## Updating remote servers

Run the following command to update from the repo:

    git pull; and django/manage.py prep; and sudo supervisorctl restart pactf 

`manage.py prep` runs the following commands:

    makemigrations
    migrate
    loadprobs
    collectstatic
    
If you are not using superisor, restart Gunicorn yourself.

For updating ngxinx configs, run the following command:

    sudo nginx -t; and sudo service nginx restart
