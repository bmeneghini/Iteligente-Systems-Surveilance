#########################################################################
# Student name: Bernardo Meneghini Muschioni V7NMZ0			#
#									#
# The file net.json contains 2 default configuration examples.		#
# the first one been valid and the second invalid, for test proporses.  #
#									#
# All the expected erros are handled on the applications. We just need	#
# to provide wrong input parameters, wrong IO path, file name to see it.#
#########################################################################

# Test inputs and parameterized test run commands:

nano net.json

#########################################################################

python3 get_users.py -v -o /home/meres/Desktop/results --source net.json

cd /home/meres/Desktop/results | nano localhost.json


#########################################################################

python3 get_users.py -o /home/meres/Desktop/results --source net.json

cd /home/meres/Desktop/results | nano localhost.json

#########################################################################

python3 get_users.py -o /home/meres/Desktop/results --source error.json