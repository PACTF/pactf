#!/usr/bin/python

def grade(arg, key):
	try:
		if int(key) == 2: return True, "Isn't that neat?"
		else: return False, "Nope!"
	except ValueError as e:
		return False, "That isn't a number!"
