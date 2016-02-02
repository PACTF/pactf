# PACTF (Beta)

# Host Documentation

### Installation

Get access to our top-secret Google Doc called "Deployment Instructions" and follow those steps.


### Throwing away current database during development

1. Delete all files from migrations
1. Run `manage.py reset_db`
1. Run `manage.py makemigrations`
1. Run `manage.py migrate`
1. Run `manage.py reloaddata`
1. Run `manage.py prep`

In dire circumstances, use `initializedb.sql`.


### Updating remote servers

1. Pull from your origin repo using `git pull`
1. Prep for deployment using `manage.py prep`, which runs the following commands for you:

        makemigrations
        migrate
        loadprobs
        collectstatic
    
1. Restart Gunicorn via Supervisor or yourself (using `supervisorctl restart pactf`)
1. (If needed:) Validate and update nginx configuration using: `sudo nginx -t; and sudo service nginx restart`


## Problem Writer Documentation

Set variables in `local_settings.py` appropriately. In `PROBLEMS_DIR`, place ‘problem folders’. Each such folder contains `problem.yaml`, `grader.py`, (optionally) a `static` folder, and (recommendedly) a `.uuid` file.

The `grader.py` file must have a `grade(team_id, submission)` function.

The `problem.yaml` file must have `name`, `point`, `description` and `hint` fields. The `description` and `hint` fields are to be written in non-HTML markdown.

The `id` field is ~~deprecated~~ obsolete. Instead, if a `.uuid` file exists, it will be used to create or update a problem. If such a file doesn't exist, one will be created by `manage.py loadprobs`.

**Static files** will be copied automatically from the problem `static` folder to the `ctfproblems/<problem-uuid>` deployment static folder. Static files can be linked to using the `{% ctfstatic 'filename.ext' %}` tag.

`loadprobs` creates or updates problems, but it doesn't delete them. To delete a problem, remove it from the database manually, and get rid of its now redundant static files by running `collectstatic --clear`.  
 
 
