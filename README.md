# PACTF (Alpha)

## Installation

- Activate a virtual environment with Python 3.5+
- `pip install -r requirements.txt`
- Create pactf_web/local_settings.py and .env
- Directly run using `run_gunicorn.fish` (TODO: support bash)
- (Optional:) Configure nginx to reverse proxy gunicorn via a sockfile


## Updating remote servers

Run `manage.py prep`. Alternatively and equivalent, run the following commands in a `manage.py` shell:

    makemigrations
    migrate
    loadprobs
    collectstatic
    
Restart Gunicorn, and new files should begin to be served.
