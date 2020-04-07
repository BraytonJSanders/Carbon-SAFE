import streamlit as st
import pandas as pd
import CarbonSafeFunctions as csf
import math

from SideBar import ModelConstants

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class default_values: # Value, Min, Max
	df = pd.DataFrame([[5000.0, 1000.0, 20000.0],
						[5000.0, 1000.0, 20000.0],
						[250000.0, 50000.0, 500000.0],
						[100000.0, 50000.0, 150000.0],
						[0.5, 0.0, 5.0]],
						columns = ['Values', 'Min', 'Max'],
						index = ['CCS Storage Site Pipeline, Non-Power O&M ($/mile-yr)',
								'EOR Sales Pipeline, Non-Power O&M ($/mile-yr)',
								'CAPEX of Meters/Gauges ($/unit)', 
								'Fixed Booster Pump CAPEX ($/station)',
								'Meters/Gauges Non-Power O&M Rate (%CAPEX)'])
values = default_values()
raw_values = values.df.copy()
indexes = values.df.index
value_column = values.df.columns[0]
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

def set_values(reset_message):
	global values
	global raw_values
	global value_column

	inside = 0

	if st.checkbox('Pipeline Systems Parameters:'):
		inside = 1
		for name in values.df.index:
			values.df.loc[name, value_column] = st.slider(name, values.df.loc[name, 'Min'], values.df.loc[name, 'Max'], values.df.loc[name, value_column], values.df.loc[name, value_column] / 100)
			st.write('')
		if st.button("*Restet to default"):
			values.df = raw_values
			st.success(reset_message)
		csf.main_body_divider()
	return inside
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class PipelineSystems:
	def __init__(self, reset_message, TaxCredits, CaptureFacilities, ScenarioData):
		self.inside = set_values(reset_message)
		
		global values
		global indexes
		global value_column

		self.data = values.df[value_column]
		self.CCS_pipe = values.df.loc[indexes[0], value_column]
		self.EOR_pipe = values.df.loc[indexes[1], value_column]
		self.meters_gauges = values.df.loc[indexes[2], value_column]
		self.fixed_CAPEX = values.df.loc[indexes[3], value_column]
		self.meters_gauges_OM_rate = values.df.loc[indexes[4], value_column] / 100

		self.count_meters = min(1, ScenarioData.storage_pipe) + min(1, ScenarioData.sales_pipe) + 1
		self.count_boosters = (math.ceil(ScenarioData.storage_pipe / 90) - 1) + (math.ceil(ScenarioData.sales_pipe / 90) - 1)

		self.projected_CO2 = CaptureFacilities.daily_CO2_capture * 17.483 * (2.2 / 2) * ModelConstants.to_kilo
		self.pipe_capacity_factor = 1 / ScenarioData.efficiency
		self.pipe_capacity = round(self.pipe_capacity_factor * self.projected_CO2 / 5, 0) * 5

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #








