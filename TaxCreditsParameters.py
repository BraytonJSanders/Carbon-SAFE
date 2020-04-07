import streamlit as st
import pandas as pd
import CarbonSafeFunctions as csf

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class default_values: # Value, Min, Max
	df = pd.DataFrame([[80.0, 0.0, 99.0],
						[50.0, 1.0, 99.0],
						[15.0, 1.0, 50.0],
						[1.1238, 0.0, 5.0],
						[11.24, 5.0, 30.0],
						[35.0, 10.0, 50.0],
						[22.66, 10.0, 30.0],
						[50.0, 20.0, 80.0]],
						columns = ['Values', 'Min', 'Max'],
						index = ['ITC Eligble Share of CAPEX (% Hard Costs)', 'Income Tax Depreciation Basis Adjustment ($)', 'Investment Tax Credit Rate (%)',
								'45Q - Inflation Adjustment Factor', '(Future 45Q Only) CO2 to EOR Year One', '(Future 45Q Only) CO2 to EOR Year End',
								'(Future 45Q Only) Saline Year One', '(Future 45Q Only) Saline Year End'])
values = default_values()
raw_values = values.df.copy()
indexes = values.df.index
value_column = values.df.columns[0]
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

def set_value(reset_message):
	global values
	global raw_values
	global value_column

	inside = 0
	if st.checkbox('Tax Credits Parameters:'):
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

class TaxCredits:
	def __init__(self, reset_message):
		self.inside = set_value(reset_message)
		global values
		global indexes
		global value_column

		self.data = values.df[value_column]
		self.ITC_CAPEX = values.df.loc[indexes[0], value_column] / 100
		self.income_dep = values.df.loc[indexes[1], value_column] / 100
		self.invest_tax_cred = values.df.loc[indexes[2], value_column] / 100
		self.adjust_45Q = values.df.loc[indexes[3], value_column]
		self.CO2_one = values.df.loc[indexes[4], value_column]
		self.CO2_end = values.df.loc[indexes[5], value_column]
		self.saline_one = values.df.loc[indexes[6], value_column]
		self.saline_end = values.df.loc[indexes[7], value_column]
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #


