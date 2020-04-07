import streamlit as st
import pandas as pd

from CarbonSafeFunctions import main_body_divider

class default_values: # Value, Min, Max
	df = pd.DataFrame([[0.0001, 0.0, 5.0],
						[1.0, 0.0, 10.0],
						[50.0, 1.0, 80.0],
						[3.5, 1.0, 20.0],
						[10.0, 1.0, 50.0],
						[1500.0, 1.0, 10000.0],
						[100.0, 20.0, 100.0],
						[20.0, 1.0, 60.0],
						[6.0, 0.0, 20.0],
						[1.5, 0.0, 10.0],
						[45.0, 0.0, 80.0]],
						columns = ['Values', 'Min', 'Max'],
						index = ['Underwrite Insurance Fee (%CAPEX)', 'Basic Industrial Insurance Annual Premium (%CAPEX)', 'Industrial Insurance Complexity & Contingency Factor (%)',
								'PISC Fund Return (%/yr)', 'PISC Trust Fund Contingency (%)', 'Long Term Liabiliy Maximum Possible Loss ($MM)',
								'Share of Possible Loss Carried by Project (%)', 'Long Term Liability Contingency Factor (%)', 'LTL Trust Fund Returns (%/yr)', 'LTL Inflation Expectation (%/yr)',
								'Proability Weight (% Chance of Event)'])
values = default_values()
raw_values = values.df.copy()
indexes = values.df.index
value_column = values.df.columns[0]


def set_values(reset_message):
	global value
	global raw_values
	global value_column

	inside = 0

	if st.checkbox('Insurance, PISC, & LTL Parameters:'):
		inside = 1
		for name in values.df.index:
			values.df.loc[name, value_column] = st.slider(name, values.df.loc[name, 'Min'], values.df.loc[name, 'Max'], values.df.loc[name, value_column], values.df.loc[name, value_column] / 100)
			st.write('')
		if st.button("*Restet to default"):
			values.df = raw_values
			st.success(reset_message)
		main_body_divider()
	return inside


class InsurancePiscLtl:
	def __init__(self, reset_message):
		global value
		global indexes
		global value_column

		self.inside = set_values(reset_message)

		self.data = values.df[value_column]
		self.underwrite = round(values.df.loc[indexes[0], value_column] / 100, 3)
		self.basic_premium = values.df.loc[indexes[1], value_column]
		self.insurance_cont = values.df.loc[indexes[2], value_column]
		self.adjusted_premium = ((self.basic_premium / 100) * (1 + (self.insurance_cont / 100)))
		self.PISC_return = values.df.loc[indexes[3], value_column] / 100
		self.PISC_cont = values.df.loc[indexes[4], value_column] / 100
		self.max_loss = values.df.loc[indexes[5], value_column]
		self.share_loss = values.df.loc[indexes[6], value_column] / 100
		self.LTL_cont = values.df.loc[indexes[7], value_column] / 100
		self.LTL_return = values.df.loc[indexes[8], value_column] / 100
		self.LTL_inflation = values.df.loc[indexes[9], value_column] / 100
		self.chance_event = values.df.loc[indexes[10], value_column] / 100
		self.max_loss_res = self.max_loss * self.share_loss








