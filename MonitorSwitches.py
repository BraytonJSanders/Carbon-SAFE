import streamlit as st
import pandas as pd
import numpy as np
import CarbonSafeFunctions as csf

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class default_values:
	default = { 'Periodic Monitoring Year?' : [2, 5],
				'Is Post Injection Survey Year?': [0, 7]}
value = default_values()
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

def set_values(MainOptions, reset_message):
	global value
	inside = 0

	if st.checkbox('Monitoring Options:'):
		inside = 1
		value.default['Periodic Monitoring Year?'][0] = st.slider('How many years do you initially need to monitor (Seismic/VSP)?', 1, 10, value.default['Periodic Monitoring Year?'][0], 1)
		value.default['Periodic Monitoring Year?'][1] = st.slider('How often do you periodically need to monitor (Seismic/VSP)?', 1, 10, value.default['Periodic Monitoring Year?'][1], 1)
		value.default['Is Post Injection Survey Year?'][1] = st.slider('How often do you periodically need to survey (Seismic/VSP)?', 1, 15, value.default['Is Post Injection Survey Year?'][1], 1)
		
		if st.button("*Restet to default"):
			value.default = { 'Periodic Monitoring Year?' : [2, 5],
							'Is Post Injection Survey Year?': [0, 7]}
			st.success(reset_message)
		csf.main_body_divider()

	switches_array = np.zeros((4, MainOptions.total_life))

	switches_array[0, :MainOptions.in_operation] = 1
	switches_array[1, MainOptions.in_operation:MainOptions.total_life] = 1
	switches_array[2, 1:value.default['Periodic Monitoring Year?'][0]+1] = 1

	for i in range(1, MainOptions.total_life):
		if np.mod(i, value.default['Periodic Monitoring Year?'][1]) == 0:
			switches_array[2, i] = 1
		if np.mod(i, value.default['Is Post Injection Survey Year?'][1]) == 0:
			switches_array[3, i] = 1
	return [switches_array, inside]

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class MonitorSwitchesData:
	def __init__(self, MainOptions, reset_message):

		switches_array = set_values(MainOptions, reset_message)
		self.inside = switches_array[-1]
		switches_array = switches_array[0]

		self.switches_df = pd.DataFrame(switches_array, index = ['In Operation', 'Closed', 'Periodic Monitoring', 'Survey Year'])
		self.in_ops = switches_array[0,:]
		self.closed = switches_array[1,:]
		self.monitor = switches_array[2,:]
		self.survey = switches_array[3,:]
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

