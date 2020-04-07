from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import math
import CarbonSafeFunctions as csf

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class ModelConstants:
	days_per_year = 365.25 # Average days per year
	hours_per_day = 24 # Hours per day
	hours_per_year = days_per_year * hours_per_day # Average hours per year
	minutes_per_year = hours_per_year * 60 # Average minutes per year
	minutes_per_day = hours_per_day * 60 # Minutes per day
	out_MM = 1 / 1000000 # Converst normal to MM
	to_MM = 1000000  # Convert MM to normal  (backwards.. in know, shit)
	to_kilo = 1 / 1000 # Convert normal to Kilo (M)
	out_kilo = 1000 # Convert Kilo to normal
	mmbtu_to_mcd = 0.9756 # MMBtu to Mcf
	gal_per_m3 = 264.172  # Gallons to Meters cubed
	psi_to_Mpa = 0.00689475729
	def to_K(F):
		return (((F - 32) * 5 / 9) + 273.15)
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class SelectBoxOptions:
	yes_no = ['Yes', 'No']
	no_yes = ['No', 'Yes']

	tons_units = ["Metric Tonnes", "Short Tonnes"]

	CoGen_Options = ['YES, Steam + Power', 'NO, Steam Only (Gas)', 'NO, Plant Steam (Coal)']
	CoGen_Size_Options = ['IECM (43.95%)', 'Petra Nova (29.17%)']
	
	Tax_45Q_Options = ['Status Quo 45Q', '45Q w/No Cap', '"Future Act" 45Q', 'No 45Q/Tax Credits']

	Share_CO2_to_EOR_Options = ['Constant Share', 'Custom Share']

	CO2_to_EOR_Price_Path = ['Tried to WTI Crude', 'Fixed Price']

	Realize_Offset_Green_Elec = ['YES, Both', 'NO, One or the Other']
	no_What_Applies = ['Tradeable Offsets', 'Green Electrons']

	Elec_Power_Rates = ['Industrial', 'Wholesale']
	NG_Power_Rates = ['Henry Hub', 'Commercial', 'Industrial']

	macrs_0 = [0, 3, 5, 7, 10, 15, 20, '5 + Bonus']
	macrs_3 = [3, 0, 5, 7, 10, 15, 20, '5 + Bonus']
	macrs_5 = [5, 0, 3, 7, 10, 15, 20, '5 + Bonus']
	macrs_7 = [7, 0, 3, 5, 10, 15, 20, '5 + Bonus']
	macrs_10 = [10, 0, 3, 5, 7, 15, 20, '5 + Bonus']
	macrs_15 = [15, 0, 3, 5, 7, 10, 20, '5 + Bonus']
	macrs_20 = [20, 0, 3, 5, 7, 10, 15, '5 + Bonus']
	macrs_Bonus = ['5 + Bonus', 0, 3, 5, 7, 10, 15, 20]

	energy_path = csf.import_energy_paths('Price_Paths')

	energy_paths = {}
	for path in energy_path:
		fresh_list = energy_path.copy()
		fresh_list.remove(path)
		fresh_list.insert(0,path)
		energy_paths[path] = fresh_list
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class MainOptions:
	def __init__(self, Power_Plants_Data):
		st.sidebar.title("Main Selection Options:")
		self.current_year = datetime.today().year
		self.plant_data = Power_Plants_Data
		self.possible_plants = Power_Plants_Data.index
		self.scenario = st.sidebar.selectbox("What Power Plant Unit Scenario?", Power_Plants_Data.index)

		st.sidebar.text('Plant Life Cycle:')
		self.in_operation = st.sidebar.slider("How many years will the plant be in operation?", 10, 75, 25, 1) + 1
		self.post_closer = st.sidebar.slider("How many years post closure need to be monitored?", 15, 150, 50, 1)
		self.total_life = self.in_operation + self.post_closer
		self.year_zero = st.sidebar.slider("What year will the project be operational?", self.current_year, self.current_year+10, self.current_year+5, 1)
		st.sidebar.text("Total length: " + str(self.total_life-1) + " years") # Display length so user can visually see the number of year
		csf.sidebar_divider()
		
		st.sidebar.text("Model Units:")
		self.tons_units = 2204.62 if st.sidebar.selectbox("Short or Metric Tonnes?", SelectBoxOptions.tons_units) == SelectBoxOptions.tons_units[0] else 2000
		csf.sidebar_divider()

		st.sidebar.text("CO2 and EOR:")
		self.CO2_path = st.sidebar.selectbox("Select the CO2 to EOR Pricing Path", SelectBoxOptions.CO2_to_EOR_Price_Path)
		self.CO2_share = st.sidebar.selectbox("Path for Share of CO2 Sales to EOR", SelectBoxOptions.Share_CO2_to_EOR_Options)
		self.CO2_share_constant = st.sidebar.slider("- - - Whats is the constant percentage?", 60.0, 100.0, 95.0, 0.5) / 100 if self.CO2_share == SelectBoxOptions.Share_CO2_to_EOR_Options[0] else np.nan
		csf.sidebar_divider()

		st.sidebar.text("CoGen Plant:")
		self.cogen_scenario = st.sidebar.selectbox("Use CoGen Power Plant for CCS?", SelectBoxOptions.CoGen_Options)
		self.cogen_size = st.sidebar.selectbox("What is the CoGen Sizing Assumption?", SelectBoxOptions.CoGen_Size_Options) if self.cogen_scenario == SelectBoxOptions.CoGen_Options[0] else np.nan
		self.cogen_macrs = st.sidebar.selectbox("What is the CoGen Plant MACRS Schedule? (years)", SelectBoxOptions.macrs_15) if self.cogen_scenario == SelectBoxOptions.CoGen_Options[0] else np.nan
		self.aux_boiler_macrs = st.sidebar.selectbox("What is the Aux Steam Boiler MACRS Schedule? (years)", SelectBoxOptions.macrs_15) if self.cogen_scenario != SelectBoxOptions.CoGen_Options[0] else np.nan
		csf.sidebar_divider()

		st.sidebar.text("Flue-Gas Tie-In with CoGen Plant:")
		self.flue_scenario = st.sidebar.selectbox("Installing a Flue-Gas Tie-In?", SelectBoxOptions.yes_no)
		self.flue_macrs = st.sidebar.selectbox("What is the Flue Tie-In MACRS Schedule? (years)", SelectBoxOptions.macrs_7) if self.flue_scenario == 'Yes' else np.nan
		csf.sidebar_divider()

		st.sidebar.text('Offsets & Green Electrons:')
		self.realize = st.sidebar.selectbox('Can Realize Offsets & Green Electrons?', SelectBoxOptions.Realize_Offset_Green_Elec)
		self.realize_one = st.sidebar.selectbox('- - - Which One Applies?', SelectBoxOptions.no_What_Applies) if self.realize == SelectBoxOptions.Realize_Offset_Green_Elec[-1] else np.nan
		csf.sidebar_divider()

		st.sidebar.text('45Q Tax Credits:')
		self.tax_45Q = st.sidebar.selectbox("What is the satus of the 45Q Tax Credits?", SelectBoxOptions.Tax_45Q_Options)
		self.tax_45Q_status_quo_max_date = st.sidebar.slider("- - - What is the 45Q Status Quo Max Out Date (Year)?", float(self.current_year), float(self.current_year+15), float(self.current_year+1), 0.25) if self.tax_45Q == SelectBoxOptions.Tax_45Q_Options[0] else np.nan
		self.tax_45Q_year_one = st.sidebar.slider("- - - What is the first year of the enactment?", self.current_year, self.current_year+15, self.current_year+5, 1) if self.tax_45Q == SelectBoxOptions.Tax_45Q_Options[2] else np.nan
		self.tax_45Q_year_last = st.sidebar.slider("- - - What is the last year of the enactment?", self.tax_45Q_year_one, self.tax_45Q_year_one+20, self.tax_45Q_year_one+5, 1) if self.tax_45Q == SelectBoxOptions.Tax_45Q_Options[2] else np.nan
		self.tax_45Q_claimed = st.sidebar.slider("- - - How many years can the credits be claimed for?", 1, 30, 12, 1) if self.tax_45Q == SelectBoxOptions.Tax_45Q_Options[2] else np.nan
		csf.sidebar_divider()

		st.sidebar.text('Water Cooling Tower:')
		self.cooling_tower_scenario = st.sidebar.selectbox("Installing a Water Cooling Tower?", SelectBoxOptions.yes_no)
		self.cooling_tower_macrs = st.sidebar.selectbox("What is the  Cooling Tower MACRS Schedule? (years)", SelectBoxOptions.macrs_5) if self.cooling_tower_scenario == 'Yes' else np.nan
		csf.sidebar_divider()

		st.sidebar.text('Water Treatment & Demin. Plant:')
		self.water_demin_scenario = st.sidebar.selectbox("Installing Water Treatment & Demin. Plant?", SelectBoxOptions.yes_no)
		self.water_demin_macrs = st.sidebar.selectbox("What is the Water Treatment Plant MACRS Schedule? (years)", SelectBoxOptions.macrs_15) if self.water_demin_scenario == 'Yes' else np.nan
		csf.sidebar_divider()

		st.sidebar.text('Compression and Dehydration Equipment:')
		self.comp_dehy_scenario = st.sidebar.selectbox("Installing Compression and Dehydration Equipment?", SelectBoxOptions.yes_no)
		self.comp_dehy_macrs = st.sidebar.selectbox("What is the Comp. Dehy. Equipment MACRS Schedule? (years)", SelectBoxOptions.macrs_15) if self.comp_dehy_scenario == 'Yes' else np.nan
		csf.sidebar_divider()

		st.sidebar.text('Electricity & Natural Gas Rates:')
		self.elec_purchase = st.sidebar.selectbox("What rate is power purchased at?", SelectBoxOptions.Elec_Power_Rates)
		self.elec_sold = st.sidebar.selectbox("What rate is power sold at?", SelectBoxOptions.Elec_Power_Rates)
		self.gas_purchase = st.sidebar.selectbox("What rate is gas purchased at?", SelectBoxOptions.NG_Power_Rates)
		csf.sidebar_divider()

		st.sidebar.text('Other MACRS Options:')
		self.storage_pipe_macrs = st.sidebar.selectbox("What is the CCS Storage Site Pipeline MACRS Schedule? (years)", SelectBoxOptions.macrs_15)
		self.eor_pipe_macrs = st.sidebar.selectbox("What is the EOR Sales Pipeline MACRS Schedule? (years)", SelectBoxOptions.macrs_15)
		self.meters_boosters_macrs = st.sidebar.selectbox("What is the CO2 Meters & Booster Stations MACRS Schedule? (years)", SelectBoxOptions.macrs_7)
		self.pre_site_macrs = st.sidebar.selectbox("What is the Pre-Injection Site MACRS Schedule? (years)", SelectBoxOptions.macrs_3)
		self.well_CAPEX_macrs = st.sidebar.selectbox("What is the MACRS Schedule for Well CAPEX? (years)", SelectBoxOptions.macrs_15)
		self.amine_capture_macrs = st.sidebar.selectbox("What is the MHI/Amine Capture Facility MACRS Schedule? (years)", SelectBoxOptions.macrs_20)
		csf.sidebar_divider()

		st.sidebar.title('')
		st.sidebar.text('University of Wyoming')
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

