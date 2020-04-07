import streamlit as st
import pandas as pd
import math

def main_body_divider():
	st.write("_______")

class default_values: # Value, Min, Max
	df = pd.DataFrame([[1.0, 0.0, 10.0],
						[0.0001, 0.0, 50.0],
						[3.0, 1.0, 20.0],
						[0.0001, 0.0, 100.0],
						[0.0001, 0.0, 100.0],
						[50.0, 1.0, 100.0],
						[0.0001, 0.0, 100.0],
						[1.5, 0.0, 10.0],
						[2.5, 0.0, 20.0],
						[0.5, 0.0, 10.0],
						[1.5, 0.0, 10.0]],
						columns = ['Values', 'Min', 'Max'],
						index = ['Number of Debt Payments in Reserve', 'Share of Year One O&M in Reserve', 'Return on Reserve Accounts',
								'Grant for Pre-Injection Site Char ($MM)', 'Other DOE Cost Share ($MM)', 'Premium for Green Power "Storage"',
								'Storage -Tradable Offset Value ($/tCO2)', 'Offset Value Escalation (%/year)', 'CO2-EOR Fixed Price ($/Mcf)',
								'CO2-EOR Tied Transport($/Mcf)', 'CO2-EOR Tied Commodity (% WTI)'])
values = default_values()
raw_values = values.df.copy()
indexes = values.df.index
value_column = values.df.columns[0]

def set_values(reset_message):
	global values
	global raw_values
	global value_column

	inside = 0
	if st.checkbox('Revenue and Reserves Parameters:'):
		inside = 1
		for name in values.df.index:
			values.df.loc[name, value_column] = st.slider(name, values.df.loc[name, 'Min'], values.df.loc[name, 'Max'], values.df.loc[name, value_column], values.df.loc[name, value_column] / 100)
			st.write('')
		if st.button("*Restet to default"):
			values.df = raw_values
			st.success(reset_message)
		main_body_divider()
	return inside

class RevenueReserves:
	def __init__(self, reset_message):
		global values
		global indexes
		global value_column

		self.inside = set_values(reset_message)

		self.data = values.df[value_column]
		self.debt_reserves = int(round(values.df.loc[indexes[0], value_column],0))
		self.OM_reserves = round(values.df.loc[indexes[1], value_column], 2) / 100
		self.reserves_return = values.df.loc[indexes[2], value_column]
		self.grant = round(values.df.loc[indexes[3], value_column], 2)
		self.other_share = round(values.df.loc[indexes[4], value_column], 2)
		self.green_premium = values.df.loc[indexes[5], value_column] / 100
		self.tradeable_value = round(values.df.loc[indexes[6], value_column], 2)
		self.tradeable_escalation = values.df.loc[indexes[7], value_column] / 100
		self.CO2_fixed = values.df.loc[indexes[8], value_column]
		self.CO2_transport = values.df.loc[indexes[9], value_column]
		self.CO2_WTI = values.df.loc[indexes[10], value_column] / 100


