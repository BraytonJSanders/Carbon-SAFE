import streamlit as st
import pandas as pd

def main_body_divider():
	st.write("_______")

class default_values: # Value, Min, Max
	df = pd.DataFrame([[30.0, 1.0, 75.0],
						[6.0, 1.0, 20.0],
						[21.0, 5.0, 50.0],
						[20.0, 5.0, 40.0],
						[1.25, 1.0, 3.0],
						[8.0, 2.0, 20.0]],
						columns = ['Values', 'Min', 'Max'],
						index = ['Share of Debt (%)', 'Cost of Debt (rd, %)', 'Corporate Tax Rate (%)', 'Loan/Bond Tenor (years)',
								'Syndicated Loan Min. 10yr DSCR', 'Expected Return on FCFE'])
values = default_values()
raw_values = values.df.copy()
indexes = values.df.index
value_column = values.df.columns[0]

def set_values(reset_message):
	global values
	global raw_values
	global value_column

	inside = 0

	if st.checkbox('Capital Structure Parameters:'):
		inside = 1
		# main_body_divider()
		for name in values.df.index:
			values.df.loc[name, value_column] = st.slider(name, values.df.loc[name, 'Min'], values.df.loc[name, 'Max'], values.df.loc[name, value_column], values.df.loc[name, value_column] / 100)
			st.write('')
		if st.button("*Restet to default"):
			values.df = raw_values
			st.success(reset_message)
		main_body_divider()
	return inside



class CapitalStructure:
	def __init__(self, reset_message):
		global values
		global indexes
		global value_column

		self.inside = set_values(reset_message)

		self.data = values.df[value_column]
		self.share_debt = values.df.loc[indexes[0], value_column] / 100
		self.cost_debt = values.df.loc[indexes[1], value_column] / 100
		self.tax_rate = values.df.loc[indexes[2], value_column] / 100
		self.loan_length = values.df.loc[indexes[3], value_column]
		self.DSCR = values.df.loc[indexes[4], value_column]
		self.FCFE_rate = values.df.loc[indexes[5], value_column]




