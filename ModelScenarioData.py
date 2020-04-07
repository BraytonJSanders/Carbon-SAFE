import webbrowser as wb
import streamlit as st
import pandas as pd
import numpy as np

from SideBar import ModelConstants
import CarbonSafeFunctions as csf

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

def set_values(Power_Plants_Data, MainOptions, model_title):
	st.title(model_title)
	csf.main_body_divider()

	st.header("Power Plant Unit Scenario: ")
	st.subheader(MainOptions.scenario)

	if MainOptions.scenario != Power_Plants_Data.index[1]:
		website_data = csf.import_plant_websites()
		if st.button('- ' + MainOptions.scenario + ' Website'):
			wb.open(website_data.loc[MainOptions.scenario]['Website URL'], new = 2, autoraise=True)
	else:
		if st.checkbox("Personal Scenario Input Data"):
			new_data = []
			for i, name in enumerate(Power_Plants_Data.columns):
				current = float(Power_Plants_Data.loc[MainOptions.scenario][name])
				new_data.append(st.slider(name + ' Value:', current * 0.5, current * 1.5, current, current / 100))
			Power_Plants_Data.loc[MainOptions.scenario] = new_data

			if st.button("*Reset to default values?"):
				Power_Plants_Data.loc[MainOptions.scenario] = Power_Plants_Data.loc['Dry Fork Station']
				st.success("Values reset.")
	st.text('Main Selection Options in Left Sidebar')
	csf.main_body_divider()
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class ScenarioData:
	def __init__(self, Power_Plants_Data, MainOptions, model_title = 'UWyo - CarbonSAFE'):

		set_values(Power_Plants_Data, MainOptions, model_title)

		self.name_plate = Power_Plants_Data.loc[MainOptions.scenario]['Nameplate']
		self.efficiency = Power_Plants_Data.loc[MainOptions.scenario]['Cap.Factor'] # DONT NEED TO BE DIVIDED BY 100!
		self.CO2_lbs_MW = Power_Plants_Data.loc[MainOptions.scenario]['CO2 lbs/MW']
		self.flue = Power_Plants_Data.loc[MainOptions.scenario]['Min. Flue']
		self.storage_pipe = Power_Plants_Data.loc[MainOptions.scenario]['StoragePipe']
		self.sales_pipe = Power_Plants_Data.loc[MainOptions.scenario]['Sales Pipe']
		self.op_hrs_per_yr = self.efficiency * ModelConstants.hours_per_year
		
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

