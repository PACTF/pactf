
# Host Documentation

If you are looking to host your own CTF, you’ve come to to the right place! You can determine whether CTFlex is right for you by reading about its [Features](#features) and [Problem Specification](#writing-problems).

If you want to hack on CTFlex or just know how it works, read this document and then check out the [developer documentation](./dev.md).


## Features

This document shall refer to the CTF for which CTFlex is to be used as ‘your CTF.’

### Rounds, timer and windows

#### Terminology

Your CTF can consist of multiple rounds, and each is called a **Contest Windows**. Windows have a start date,  end date, a title and associated problems. Windows also have a **codename**, which is a short human-readable identifier like `crypto` or `binexp` used, for example, to refer to the window in URLs.

During each window, each team can view and solve problems only while their **Personal Timer** is running. This timer is a span of time of a shorter length than the window that the team can choose to begin at any time per their convenience.

**Note:** The front-end for CTFlex/PACTF uses the word **‘rounds’** and ‘timers’ based on what later user testing revealed to be most self-explanatory words. However, the code and documentation for CTFlex/PACTF refers to ‘rounds’ as ‘windows’ or ‘Contest Windows’ and timers as ‘Personal Timers.’


#### Possible States of the Competition

A window can be in one of the following states:

- **Waiting:** The window has not yet begun.
- **Ongoing:** The window has begun but not ended.
- **Past:** The window has ended.

While a window is ongoing, it may be further classified into one of the following states with respect to a particular team:

- **Inactive:** The team has not yet started their timer.
- **Active:** The team has started their timer, which has not yet expired.
- **Expired:** The team had started their timer, which has since expired.

Here’s a summarizing table

<table><tbody>
	<tr>
		<td rowspan=2>Waiting</td>
		<td colspan=3 align="center">Ongoing</td>
		<td rowspan=2>Past</td>
	</tr>
	<tr>
		<td>Inactive</td>
		<td>Active</td>
		<td>Expired</td>
	</tr>
	<tr>
		<td colspan=5></td>
	</tr>
</tbody></table>

#### The Current Window

The 'current' window is defined as the window that fits the first of the following criteria:

- The window is currently ongoing.
- The window is the next to begin.
- The window was the last to have ended.

### Website Pages

The website consists of multiple pages, including the:

- **Landing Page:** As the index of the website and the first thing visitors hit, this page pitches your CTF and lists the dates of its rounds.
- **Game:** This page lists the problems a team has unlocked and takes flag submissions assuming a team has started their timer which has not yet expired etc. 
- **Scoreboard:** This page ranks all teams eligible to win prizes.
- **News:** This page lists all announcements for that window.

#### Windows and the URL schema

If you visit the URL `yourctf.com/game/foo`, where `foo` is the codename of a window, CTFlex will display the Game for that particular window, and similarly for the scoreboard.

If a codename is not supplied, as in the URL `yourctf.com/game`, the user will be redirected to `yourctf.com/game/bar`  where `bar` is the codename of the current window.

The scoreboard has a special URL: `yourctf.com/scoreboard/overall`. Visiting this URL will display 
rankings across all rounds.

Both the game and scoreboard always have a **dropdown** in the header to allow competitors to switch between windows.

#### States for the Game 

The Game page displays different based on the state of the window and team:

- **Waiting:** The Game will display a countdown and ask if the competitor wants to browse other windows.
- **Inactive:** The Game will let the competitor start a timer.
- **Active:** Competitors can view and solve problems, improving their ranking.
- **Done:** Competitors cannot view problems for that round. This was decided in order to reduce confusion about when correct flag submissions improve rankings and when they don't. It also mirrors [USACO][usaco]’s Contest Windows.
- **Past:** Competitors can view problems, submit flags, and increase their displayed score, but their ranking and score on the scoreboard for that window will not change since the window has ended.

## Announcements

Announcements for a window will be displayed on the News page. Announcements can also be associated with particular problems; they will then be displayed inline with the problems on the Game page.

To make an announcement, run `manage.py announce foo.yaml` where `foo.yaml` file follows the format:

    id: 102  # This field is optional but recommended
    title: You can use Markdown here
    
    window: web
    problems:  # This field is optional
      - 51e7003e-d833-4dd8-b241-cf744965cd56
    
    body: >
        You can use Markdown here too.

 
**Note:** The front-end for CTFlex/PACTF uses the word **‘news’** based on what later user testing revealed to be most self-explanatory word. However, the code and documentation for CTFlex/PACTF uses the word ‘announcement’.


## Using CTFlex

### Installation and Configuration

#### With PACTF Web

PACTF Web is a sample project that makes use of CTFlex. It might be a good idea to try to run PACTF Web yourself to understand how to use CTFlex. You can also just modify parts of PACTF Web to have an entire website for your CTF.

**If you are familiar with Django, have your server already set-up, and want to CTFlex independently of PACTF Web, skip to [Using CTFlex](#independently-of-pactf-web).**

For now, instructions for installing and running PACTF starting from a fresh server are hosted on a [Google Doc][deployment].

PACTF Web uses `django-configuration` and `envdir` for defining settings. You may either edit `settings.py` and set attributes in the `Django` class or create a file in `django/pactf/envdir` whose name is the name of a setting and whose contents are the setting value.


#### Independently of PACTF Web

Clone CTFlex locally and add it to the Python path. Then configure your project settings as follows:

Add `ctflex` to `INSTALLED_APPS`. It must come after any apps of yours that override CTFlex templates.

Add `ctflex.middleware.RatelimitMiddleware` to `MIDDLEWARE_CLASSES` as so:

	MIDDLEWARE_CLASSES = (
	        # Django Defaults
	        'django.contrib.sessions.middleware.SessionMiddleware',
	        'django.middleware.common.CommonMiddleware',
	        'django.middleware.csrf.CsrfViewMiddleware',
	        'django.contrib.auth.middleware.AuthenticationMiddleware',
	        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
	        'django.contrib.messages.middleware.MessageMiddleware',
	        'django.middleware.clickjacking.XFrameOptionsMiddleware',
	        'django.middleware.security.SecurityMiddleware',
	
	        # CTFlex
	        'ctflex.middleware.RatelimitMiddleware',
	        
	        # Local
	        'ctflex.middleware.IncubatingMiddleware',
	    )

Add `ctflex.views.default_context` to `TEMPLATES` as so:

	TEMPLATES = [
	        {
	            'BACKEND': 'django.template.backends.django.DjangoTemplates',
	            'APP_DIRS': True,
	            'OPTIONS': {
	                'context_processors': [
	                    # Django Defaults
	                    'django.template.context_processors.debug',
	                    'django.template.context_processors.request',
	                    'django.contrib.auth.context_processors.auth',
	                    'django.contrib.messages.context_processors.messages',
	
	                    # CTFlex
	                    'ctflex.views.default_context'
	                ],
	            },
	        },
	    ]

Define some URLs:

	LOGIN_URL = 'ctflex:login'
    LOGOUT_URL = 'ctflex:logout'
    LOGIN_REDIRECT_URL = 'ctflex:index'

Configure problem loading and static files:

	CTFLEX_PROBLEMS_DIR = values.Value(join(BASE_DIR, 'ctfproblems'), environ_prefix=ctflex_prefix)
    CTFLEX_PROBLEMS_STATIC_DIR = join(CTFLEX_PROBLEMS_DIR.value, '_static')
    CTFLEX_PROBLEMS_STATIC_URL = 'ctfproblems'

Add `(CTFLEX_PROBLEMS_STATIC_URL, CTFLEX_PROBLEMS_STATIC_DIR)` to `STATICFILES_DIRS` as so:

	STATICFILES_DIRS = (
		# CTFlex
        (CTFLEX_PROBLEMS_STATIC_URL, CTFLEX_PROBLEMS_STATIC_DIR)
    )

A full list of other settings you can define is available in `django/ctflex/settings.py`.

You must create at least one window before running your project. Otherwise, the behavior of CTFlex is undefined.

#### Customizing CTFlex further

You should not need to modify any source code of the CTFlex app. It is recommended not to so that you can receive updates for CTFlex, and diagnose problems more easily because you are using the same unmodified CTFlex as others. If you genuinely do want to achieve something for which you would need to modify or duplicate CTFlex functionality, consider contributing that change back to CTFlex by reading the [developer documentation](./dev.md).  

To change just the look or content of a page, yoyou can inspect what [template](https://docs.djangoproject.com/en/1.9/topics/templates/) and static scripts or stylesheets CTFlex uses for that page. Then you can create templates, stylesheets or scripts of that same name in your app’s `templates` or `static` folder. So if you were overriding a templates stored in `ctflex/templates/ctflex/foo/bar.html`, you would create the template `yourctf/templates/ctflex/foo/bar.html`. Some templates in particular that you might want to change are:

- `templates/ctflex/base/footer.snippet.html`
- `templates/ctflex/text/*`
- `templates/ctflex/text/base.template.html`
- `static/ctflex/css/*`

If you want to change some behavior for a URL, in your project’s `urls.py`, where you include all of CTFlex’s URLs, you can [add a preceding line](https://stackoverflow.com/a/9343212/1292652) that routes the URL to the the view CTFlex would have routed to except you decorate CTFlex’s view or entirely replace it. However, many CTFlex views [take arguments](https://docs.djangoproject.com/en/1.9/topics/http/urls/#passing-extra-options-to-view-functions) that let you customize their behavior without needing to decorate or duplicate them, so look into that first.




### Writing Problems

#### Basic Overview

Structure the folder referenced in `PROBLEMS_DIR` as so: Have directories whose names are Contest Window 'codes'. Then, in each such directory, have 'problem folders'.  Problem folders whose name begins with an underscore are ignored. In a problem folder, you must have the file `problem.yaml`, the Python script `grader.py`, (optionally) the folder `static`folder, and (recommendedly) a `.uuid` file.

The `problem.yaml` file must always have the `name` and `point` fields. It may have a `deps` field. Simple problems must contain the `description` and `hint` fields. Non-simple problems, called, dynamic problems, must contain the `dynamic` field.

The `grader.py` file must have a `_grade(key, submission)` function. The parameter `key` is a hash of the team id and a salt.

If a `.uuid` file exists, then if a problem with the same UUID already exists, that problem will be updated; else, a new problem will be created with the gien UUID. If a `.uuid` file does not exist, one will be created on running `manage.py loadprobs`.

Static files can be linked to in the description and hint using the `{% ctfstatic '<basename>' %}` tag. Any files in the `static` folder (if it exists) to the `ctfproblems/<problem-uuid>` deployment static folder, though this implementation is irrelevant to using the feature and may change.

Run `manage.py loadprobs` to create or update problems. To delete problems not in `PROBLEMS_DIR` anymore, pass the `--clear` option.

#### Dynamic problems

The `dynamic` field is a boolean that defaults to False. If true, a Python script called `generator.py` will be looked for in the problem directory. This file must contain a `gen(key)` function that returns a 2-tuple of a description and a hint. `key` will be a hash of the team ID. The function should be deterministic upon the `key` so that users don't get different problems every time. Currently, the output is not even cached to the database for (admittedly untested) performance reasons, but problem writers do not need to worry about this. 

**If you want to use a dynamic problem but have the user login to an external website,** CTFlex and the external website need to co-ordinate. You can achieve this by giving the user a login name like `userX` where `X` is the `key`  or something generated from it, and then make the password a hash of `X` and a salt that is hardcoded in the generator and in the external system. Now the external system can behave like `grader()`.


#### Problem Dependencies

The `deps` dictionary field is used to enable a problem conditionally for competitors. It can optionally contain the `problems` field. This shall be a list of problem UUIDs relevant to determining whether the problem being loaded should be enabled for a competitor. If the `problems` field is not provided, all problems shall be considered relevant. The `deps` dictionary can optionally contain the `score` integer field. Its value is the threshold that the sum of the scores of problems considered relevant should exceed. If `score` is not provided, it defaults to 1. 


  [usaco]: https://usaco.org/
  [deployment]: https://docs.google.com/document/d/1O-HpONG-if3xE7YQqYMVFYkE4mwYZmL-9rpbEDD16M0/edit?usp=sharing