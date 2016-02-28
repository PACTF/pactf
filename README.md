# PACTF


## What is this?

This repository (currently) houses two projects:
 
- **CTFlex**, short for ‘CTF-lexible’: a reusable CTF framework written as a [Django][django] app.
- **PACTF Web**: a website for PACTF that uses CTFlex.

**PACTF** itself, short for ‘Phillips Academy CTF’, is a PvE CTF targeted at high schoolers.

Don’t know what a PvE CTF is? Read on!


### What is a CTF?

**CTFs**, short for ‘Capture the Flags,’ are a type of Computer Security competition where “you hack, decrypt, reverse, and do whatever it takes to” capture secret answer strings called ‘flags’ (to quote [PicoCTF’s website][picoctf]).

In a **PvP CTF**, teams get assigned systems and try to hack into other teams’ systems, whereas in a **PvE CTF**, teams solve puzzles all written and set-up by the contest organizers. Most high-school CTFs (including PACTF) are PvE, and this documentation only talks about PvE CTFs.

To get **flags**, you solve problems, and once you solve one, you should end up with, among other things, a string of text. This string is usually human-readable, and it almost always adheres to a predictable format, like `flag{<this_part_changes>}`. Once you think you’ve captured the flag, you can submit it online next to the problem’s description. Your submission will be graded, and, if it is correct, you will earn points and possibly unlock more problems!

You sign up for CTFs as part of a **team** of 1–5 players. Mosts CTFs award prizes to top scorers if your team is **eligible** based on its members’ locations, educational background etc. For example, for PACTF, your team has to consist of American middle- or high-schoolers to be ranked on the scoreboard and win prizes. The **scoreboard** is just that: a ranking of eligible teams.


### PACTF/CTFlex is different

From [PACTF’s website][pactf]:

> Experienced CTFer? Or new to Capture The Flags? Either way, want to solve problems and win prizes without spending fourteen consecutive days on a CTF? Check out PACTF.

> **Instead of a two-week sprint,** PACTF will have three rounds, each one week long. During each round, your team will be able to pick any two-day span to grab as many flags as you can! Choose wisely: Once your two days run out, you won’t be able to score more points in that round.

> **Don’t worry about being too slow, though!** Even if your two-day timer is over, you can still test your skills against problems in previous rounds.

> **There are scoreboards** for each individual round, and there is an overall all-time scoreboard. Prizes will be given to the top-ranking teams of the individual rounds and the overall CTF, so whether you are a specialist or an all-rounder, there's something for you!

PACTF enjoys this feature of rounds and timers grâce à CTFlex.


## Who are you?

### Want to solve computer security puzzles for fun and prizes?

Head on over to [PACTF’s website][pactf]!


### Want to host your own CTF?

Then you’ve have come to the right place!

By using CTFlex, you will be able to **focus on what’s important to _your_ CTF like writing problems,** not getting bogged down with the minutiae of of figuring out email password resets etc.

**You need not be familiar with Django** or proficient with Python to use CTFlex successfully.

Now go check out the [host documentation](docs/host.md)!


### Want to hack on CTFlex or just know how it works?
 
That’s awesome! Check out the [developer documentation](docs/devs.md).


## Who are we?

We are bunch of high-schoolers who participated in their first CTF in the Spring of 2015 and have since been driven to bring that same rewarding experience to everyone. We are:

- [Yatharth Agarwal](mailto:yagarwal@andover.edu)
- [Cameron Wong](mailto:cwong@andover.edu)
- [Tony Tan](mailto:ztan@andover.edu)

If you are using CTFlex and PACTF, we would love for you to get in touch for providing feedback or asking for support.

We were able to bring CTFlex and PACTF to you thanks to support from our school, [Phillips Academy, Andover][andover].


  [django]: https://djangoproject.org
  [picoctf]: https://picoctf.com
  [pactf]: https://pactf.com
  [andover]: https://www.andover.edu
 