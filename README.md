# PACTF (Alpha)

## Installation

- Use the [Fish shell](http://fishshell.com)
- Activate a virtual environment with Python 3.5+
- Install the requirements using `pip install -r requirements.txt`
- Create pactf_web/local_settings.py and .env
- Prep using `manage.py prep`
- (Optional:) Load fixtures using `manage.py reloaddata`
- Serve site from Gunicorn directly using `run_gunicorn.fish`
- (Optional:) Serve site using nginx (specifically, reverse proxy via a sockfile)
    - Toggle `PACTF_USE_SOCKETFILE` in `.env`
    - Create an nginx configuration file
    - Update nginx as in the Updating section
- (Optional:) Serve the site via Supervisor


## Updating remote servers

1. Pull from your origin repo using `git pull`
1. Prep for deployment using `manage.py prep`, which runs the following commands for you:

        makemigrations
        migrate
        loadprobs
        collectstatic
    
1. Restart Gunicorn via Supervisor or yourself (using `supervisorctl restart <projectname>`)
1. (If needed:) Validate and update ngxinx configuration using: `sudo nginx -t; and sudo service nginx restart`
