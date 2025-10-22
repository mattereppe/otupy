#!../../../../lycan/.venv/bin/python3
# Example to use the OpenC2 library
#

import logging
import sys
import json

import openc2
import time

from helpers import load_files

import sys
sys.path.insert(0, "../profiles/")

import acme
import mycompany
import mycompany_with_underscore
import example
import esm
import digits
import digits_and_chars

command_path_good = "openc2-commands-good"
response_path_good = "openc2-responses-good"
NUM_TESTS = 100

def main():
	cmd_files = load_files(command_path_good) 
	rsp_files = load_files(response_path_good)

	for i in range(1, NUM_TESTS+1):
		print("Running test #", i)
		for c in cmd_files:

			with open(c) as f:
				cmd_txt=f.read()

			print("Decoding started at time: ", time.time())
			cmd = openc2.parse(json.loads(cmd_txt))
			print("Decoding ended at time: ", time.time())
	
			print("Encoding started at time: ", time.time())
			json.dumps(cmd.serialize())
			print("Encoding ended at time: ", time.time())

		for r in rsp_files:

			with open(c) as f:
				rsp_txt=f.read()

			print("Decoding started at time: ", time.time())
			rsp = openc2.parse(json.loads(rsp_txt))
			print("Decoding ended at time: ", time.time())

			print("Encoding started at time: ", time.time())
			json.dumps(rsp.serialize())
			print("Encoding ended at time: ", time.time())

if __name__ == '__main__':
	main()
