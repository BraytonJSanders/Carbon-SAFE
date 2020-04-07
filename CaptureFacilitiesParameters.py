import streamlit as st
import pandas as pd
import math
import numpy as np

import CarbonSafeFunctions as csf
from SideBar import ModelConstants, SelectBoxOptions

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class default_values: # Value, Min, Max
	columns = ['Values', 'Min', 'Max']

	amine = pd.DataFrame([[1.52, 0.0, 10.0],
						[16.0, 2.0, 50.0],
						[1.13, 0.0, 10.0],
						[65.0, 20.0, 110.0]],
						columns = columns,
						index = ['CC Consumables ($/tCO2)', 'Water Usage (gal/MW-plant-hr)', 'Water Pricing ($/kgal)', 'Flue Gas Fan & Sorbent Pump (kW/MW-plant)'])

	flue_gas = pd.DataFrame([[0.5, 0.0, 5.0]],
						columns = columns,
						index = ['Non-Power O&M Factor (%CAPEX)'])

	comp_dehi = pd.DataFrame([[1.25, 1.0, 4.0],
							[10.0, 1.0, 30.0],
							[2300.0, 1000.0, 4000.0]],
							columns = columns,
							index = ['CCS Capacity Oversizing Factor', 'Inlet Pressure (psi)', 'Outlet Pressure (psi)'])

	CoGen = pd.DataFrame([[9000.0, 6000.0, 14000.0],
						[0.4, 0.0, 1.0]],
						columns = columns,
						index = ['Heat Rate (btu/kWh)', 'Factor for BOP & Other Costs'])

	aux_boiler = pd.DataFrame([[2580.0, 1000.0, 4000.0],
								[8800.0, 7800.0, 9800.0,]],
								columns = columns,
								index = ['Aux. Boiler Fuel (btu/kwh-plant)', 'BTU Rating of PRB Coal (btu/lb)'])

	cool_tower = pd.DataFrame([[541.666667, 300.0, 800.0]],
						columns = columns,
						index = ['Cooling Water Requirement (gpm/MW)'])

	water_demin = pd.DataFrame([[1.0, 1.0, 3.0],
								[0.5, 0.0, 5.0],
								[1.0, 0.0, 10.0],
								[3.5, 1.0, 15.0],
								[5.5, 1.0, 15.0]],
						columns = columns,
						index = ['Water Treatment Oversize Factor', 'Non-Power O&M Factor (%CAPEX)', 'Chemical Cost ($/m3)', 'Energy Usage (kWhs/m3)', 'Demin Energy Usage (kWhs/m3)'])

	facilities_dic = {'MHI/Amine Capture Facility': amine,
					'Flue-Gas Tie In': flue_gas,
					'Compression/Dehydration Plant': comp_dehi,
					'CoGen Steam+Power': CoGen,
					'Aux Steam Boiler or Integration': aux_boiler,
					'Cooling Tower': cool_tower,
					'Water & Demin Treatment Plants': water_demin}
values = default_values()
keys = list(values.facilities_dic.keys())
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache(suppress_st_warning=True)
def create_raw_dictionary(dictionary):
	raw_values = {}
	for facility in dictionary.keys():
		raw_values[facility] = dictionary[facility].copy()
	return raw_values
raw_values = create_raw_dictionary(values.facilities_dic)
value_column = values.columns[0]
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

def set_values(reset_message):
	global values
	global raw_values
	global value_column

	inside = 0

	if st.checkbox('Capture Facilities Parameters:'):
		inside = 1
		csf.main_body_divider()

		for facility in values.facilities_dic.keys():
			if st.checkbox('- - ' + facility):
				for name in values.facilities_dic[facility].index:
					values.facilities_dic[facility].loc[name, value_column] = st.slider(name, values.facilities_dic[facility].loc[name, 'Min'], values.facilities_dic[facility].loc[name, 'Max'], values.facilities_dic[facility].loc[name, value_column], values.facilities_dic[facility].loc[name, value_column] / 100)
				csf.main_body_divider()
		if st.button("*Reset ALL to default"):
			for facility in values.facilities_dic.keys():
				values.facilities_dic[facility] = raw_values[facility]
			st.success(reset_message)
		csf.main_body_divider()
	return inside
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class CaptureFacilities:
	def __init__(self, reset_message, MainOptions, ScenarioData, GlobalParameters, TaxCredits):
		self.inside = set_values(reset_message)
		global values
		global value_column
		global keys

		# MHI/Amine Capture Facility
		self.amine = values.facilities_dic[keys[0]][value_column]
		self.amine_consumables = self.amine.iloc[0]
		self.amine_water_use = self.amine.iloc[1]
		self.amine_fan_pump = self.amine.iloc[3]

		# Flue-Gas Tie In
		self.flue_gas = values.facilities_dic[keys[1]][value_column]
		self.flue_gas_OM_rate = self.flue_gas.iloc[0] / 100
		self.flue_stream = min(ScenarioData.name_plate * 0.85, (2000000 / ((ScenarioData.CO2_lbs_MW / MainOptions.tons_units) * ModelConstants.hours_per_year * ScenarioData.efficiency)) / (GlobalParameters.cap_eff))
		self.daily_CO2_capture = (self.flue_stream * ScenarioData.efficiency * ScenarioData.CO2_lbs_MW * 24) * GlobalParameters.cap_eff / MainOptions.tons_units
		self.CO2_per_year = self.daily_CO2_capture * ModelConstants.days_per_year * ModelConstants.out_MM
		self.project = self.daily_CO2_capture * (MainOptions.in_operation - 1) * ModelConstants.days_per_year / 1000000

		# Compression/Dehydration Plant
		self.comp_dehi = values.facilities_dic[keys[2]][value_column]
		self.comp_dehi_cap_factor = self.comp_dehi.iloc[0]
		self.comp_dehi_inlet = self.comp_dehi.iloc[1]
		self.comp_dehi_outlet = self.comp_dehi.iloc[2]
		self.max_capture = self.comp_dehi_cap_factor * self.daily_CO2_capture

		# CoGen Steam+Power
		self.CoGen = values.facilities_dic[keys[3]][value_column]
		self.CoGen_heat = self.CoGen.iloc[0]
		self.CoGen_other = self.CoGen.iloc[1]
		self.aux_nameplate = (math.ceil(0.4395 * self.flue_stream / 10) * 10) if MainOptions.cogen_size == SelectBoxOptions.CoGen_Size_Options[0] else (math.ceil(0.325 * self.flue_stream / 10) * 10)

		# Aux Steam Boiler or Integration
		self.aux_boiler = values.facilities_dic[keys[4]][value_column]
		self.aux_boiler_fuel = self.aux_boiler.iloc[0]
		self.aux_boiler_coal = self.aux_boiler.iloc[1]
		self.aux_boiler_output = self.flue_stream * ScenarioData.efficiency * ModelConstants.out_kilo * ModelConstants.hours_per_year

		# Cooling Tower
		self.cool_tower = values.facilities_dic[keys[5]][value_column]
		self.cool_tower_water_use = self.cool_tower.iloc[0]
		self.makeup_water = (self.flue_stream / 240) * MainOptions.tons_units

		# Water & Demin Treatment Plants
		self.water_demin = values.facilities_dic[keys[6]][value_column]
		self.water_demin_cap_factor = self.water_demin.iloc[0]
		self.water_demin_OM_rate = self.water_demin.iloc[1] / 100
		self.water_demin_chem_cost = self.water_demin.iloc[2]
		self.water_demin_treat_use = self.water_demin.iloc[3]
		self.water_demin_demin_use = self.water_demin.iloc[4]
		self.water_per_day = self.makeup_water * ModelConstants.minutes_per_day * ScenarioData.efficiency / ModelConstants.gal_per_m3
		self.demin_water_per_day = (16 * self.flue_stream / 240)* ModelConstants.minutes_per_day * ScenarioData.efficiency / 264.172

		self.water_price = self.amine.iloc[2]

		# CAPEX
		self.amine_CAPEX = 255000000 * (GlobalParameters.PetraNova / 240 / 1000) * (1 / ((self.flue_stream / 240) ** (1/4))) * self.flue_stream * 1000
		self.Cogen_CAPEX = max(1.31 * np.exp(8.495727-0.38014 * np.log(self.aux_nameplate)), 625 + 220) * GlobalParameters.PetraNova * (1 / (self.aux_nameplate / 70) ** (2/10)) * ModelConstants.out_kilo * self.aux_nameplate * (1 / (1 - self.CoGen_other)) if MainOptions.cogen_scenario == SelectBoxOptions.CoGen_Options[0] else 0
		self.aux_boiler_CAPEX = (((GlobalParameters.PetraNova * 41.5) if MainOptions.cogen_scenario == SelectBoxOptions.CoGen_Options[1] else 140) * self.flue_stream * ModelConstants.out_kilo) if MainOptions.cogen_scenario != SelectBoxOptions.CoGen_Options[0] else 0
		self.cool_tower_CAPEX = (154 * GlobalParameters.PetraNova * (1 / ((self.flue_stream / 240) ** (1 / 4))) * self.cool_tower_water_use * self.flue_stream) if MainOptions.cooling_tower_scenario == SelectBoxOptions.yes_no[0] else 0
		self.water_treat_CAPEX = (csf.PetraNovaCAPEX_calc(3500, GlobalParameters.PetraNova, self.flue_stream) * self.water_per_day) if MainOptions.water_demin_scenario == SelectBoxOptions.yes_no[0] else 0
		self.demin_CAPEX = (csf.PetraNovaCAPEX_calc(60000, GlobalParameters.PetraNova, self.flue_stream, power = 0) * self.demin_water_per_day) if MainOptions.water_demin_scenario == SelectBoxOptions.yes_no[0] else 0
	
		self.water_demin_CAPEX = self.demin_CAPEX + self.water_treat_CAPEX
		self.flue_gas_CAPEX = (csf.PetraNovaCAPEX_calc((15000000/240), GlobalParameters.PetraNova, self.flue_stream) * self.flue_stream) if MainOptions.flue_scenario == SelectBoxOptions.yes_no[0] else 0
		self.comp_dehi_CAPEX = (12000 * GlobalParameters.PetraNova * self.max_capture) if MainOptions.comp_dehy_scenario == SelectBoxOptions.yes_no[0] else 0

		# ITC Federal
		ITC_share = TaxCredits.ITC_CAPEX
		ITC_rate = TaxCredits.invest_tax_cred

		self.amine_ITC = csf.calc_federal_ITC(self.amine_CAPEX, ITC_share, ITC_rate)
		self.CoGen_ITC = csf.calc_federal_ITC(self.Cogen_CAPEX, ITC_share, ITC_rate)
		self.aux_boiler_ITC = csf.calc_federal_ITC(self.aux_boiler_CAPEX, ITC_share, ITC_rate)
		self.cool_tower_ITC = csf.calc_federal_ITC(self.cool_tower_CAPEX, ITC_share, ITC_rate)
		self.water_demin_ITC = csf.calc_federal_ITC(self.water_demin_CAPEX, ITC_share, ITC_rate)
		self.comp_dehi_ITC = csf.calc_federal_ITC(self.comp_dehi_CAPEX, ITC_share, ITC_rate)

		self.flue_gas_ITC = csf.calc_federal_ITC(self.flue_gas_CAPEX, ITC_share, ITC_rate)
		self.water_demin_ITC = csf.calc_federal_ITC(self.water_demin_CAPEX, ITC_share, ITC_rate)
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #





