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

Configure relevant settings in pactf/envdir.

It is recommended to structure `PROBLEMS_DIR` as so: Have directories whose names are Contest Window 'codes'. Then, in each such directory, have 'problem folders'.  Problem folders whose name begins with an underscore are ignored. In a problem folder, you must have the file `problem.yaml`, the Python script `grader.py`, (optionally) the folder `static`folder, and (recommendedly) a `.uuid` file.

The `problem.yaml` file must always have the `name` and `point` fields. It may have a `deps` field. Simple problems must contain the `description` and `hint` fields. Non-simple problems, called, dynamic problems, must contain the `dynamic` field.

The `grader.py` file must have a `grade(key, submission)` function. The parameter `key` is a hash of the team id and a salt.

For dynamic problems, the `dynamic` field is a string to a Python script called a 'generator'. It must contain a `gen(key)` function that returns a 2-tuple of a description and a hint. It must be deterministic upon the `key` so that `manage.py loadprobs` is an idempotent command. Currently, the output is not even cached to the database for (admittedly untested) performance reasons.

The `deps` dictionary field is used to enable a problem conditionally for competitors. It can optionally contain the `problems` field. This shall be a list of problem UUIDs relevant to determining whether the problem being loaded should be enabled for a competitor. If the `problems` field is not provided, all problems shall be considered relevant. The `deps` dictionary can optionally contain the `score` integer field. Its value is the threshold that the sum of the scores of problems considered relevant should exceed. If `score` is not provided, it defaults to 1. 

If a `.uuid` file exists, then if a problem with the same UUID already exists, that problem will be updated; else, a new problem will be created with the gien UUID. If a `.uuid` file does not exist, one will be created on running `manage.py loadprobs`.

Static files can be linked to in the description and hint using the `{% ctfstatic '<basename>' %}` tag. Any files in the `static` folder (if it exists) to the `ctfproblems/<problem-uuid>` deployment static folder, though this implementation is irrelevant to using the feature and may change.

`loadprobs` creates or updates problems, but it doesn't delete them. To delete a problem, remove it from the database manually, and get rid of its now redundant static files by running `collectstatic --clear`. 
 
 
