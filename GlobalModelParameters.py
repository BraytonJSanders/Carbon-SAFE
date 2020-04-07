import streamlit as st
import pandas as pd
import CarbonSafeFunctions as csf

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class default_values:
	df = pd.DataFrame([[80.0, 10.0, 99.0],
						[15.0, 1.0, 75.0],
						[10.0, 1.0, 50.0],
						[82.0, 10.0, 99.0]],
						columns = ['Values', 'Min', 'Max'],
						index = ['Gen-2 PetraNova Reduction (% of Total)', "Owner's Costs as %CAPEX", 'Minimum Carry Book Value (%)', 'MHI/Amine Capture Efficiency (%)'])
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

	if st.checkbox('Global Model Parameters:'):
		inside = 0
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

class GlobalParameters:
	def __init__(self, reset_message):
		global values
		global indexes
		global value_column

		self.inside = set_values(reset_message)

		self.data = values.df[value_column]
		self.PetraNova = values.df.loc[indexes[0], value_column] / 100
		self.owner_CAPEX =  values.df.loc[indexes[1], value_column] / 100
		self.min_book_value = values.df.loc[indexes[2], value_column] / 100
		self.cap_eff = values.df.loc[indexes[3], value_column] / 100

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #




		