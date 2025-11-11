   __          _______        _       _____  
  / _|        |__   __|      | |    _|  __ \ 
 | |_ _   _ _ __ | | ___  ___| |_  (_) |  | |
 |  _| | | | '_ \| |/ _ \/ __| __|   | |  | |
 | | | |_| | | | | |  __/\__ \ |_   _| |__| |
 |_|  \__,_|_| |_|_|\___||___/\__| (_)_____/ 
                                             
                                             


Sends http requests to endpoint for function testing on OpenFaaS. 

Execution is in “rounds”, n calls of each defined function per tier. 

Scaling processes are able to vary the proportion of executions per tier. 

Args:

Required:

	mode:
		Positional, must be first
		no keyword (no need for mode=xyz, just use the mode name)

		Modes:
			naive	- single run of all defined functions, for each tier, one time
			round     - round robin, each function/tier, repeating
			burst	- concurrent requests, tiers can be run proportionally, repeating
			ramp		- as burst, increases linearly by specified factor
			exp		- as burst, increases exponentially

Optional:
		ALL: keyword required, unordered, one space between (rounds=2 wait=1)
			rounds 	- number of rounds to repeat execution
			seconds 	- number of seconds to run for !- Overrides rounds argument
			wait 	- seconds to wait between individual requests
			pause  	- seconds to wait between rounds of execution

		Scaling: these adjust the relative amount of executions per tier in each execution round
			lx		- low tier scale value
			mx		- med tier scale value
			hx		- high tier scale value
			exp		- exponential growth value

			Behavior:
			burst	- each round will send the specified mix of low, med, high tier requests
			ramp		- as burst, each round will scale by the given value (hx=5: 5, 10, 15, 20, …)
			exp		- as ramp, but scaling is exponential based on exp variable (hx=3 exp=2: 3, 9, 27, …)	

Functions:

	Functions are defined in the functions.json. 
	Compute-Time

	{
  		"sleep": {
    		"headers": {
      		"xTier": "X-Tier",
      		"computeTime": "Compute-Time"
    			},
    		"computeSeconds": "0",
    		"body": ""
  		}
	}


Tiers:
	tiers are defined in the tiers.json file. 