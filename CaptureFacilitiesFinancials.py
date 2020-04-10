import streamlit as st
import pandas as pd
import numpy as np

import CarbonSafeFunctions as csf
from SideBar import ModelConstants, SelectBoxOptions
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache(suppress_st_warning=True)
def get_elec_rate(type_elec, fuel_data):
	return fuel_data.loc['Industrial Electricity'] if type_elec == SelectBoxOptions.Elec_Power_Rates[0] else fuel_data.loc['Commercial Electricity']
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class CaptureFacilitiesFinancial:
	def __init__(self, MainOptions, ScenarioData, FuelPrices, TimeValueMoney, MonitorSwitchesData,
								GlobalParameters, CapitalStructure, RevenueReserves, CaptureFacilities, TaxCredits):
		self.length = MainOptions.total_life
		self.MainOptions = MainOptions
		self.ScenarioData = ScenarioData
		self.FuelPrices = FuelPrices
		self.TimeValueMoney = TimeValueMoney
		self.MonitorSwitchesData = MonitorSwitchesData
		self.GlobalParameters = GlobalParameters
		self.CapitalStructure = CapitalStructure
		self.RevenueReserves = RevenueReserves
		self.CaptureFacilities = CaptureFacilities
		self.TaxCredits = TaxCredits

		self.in_ops = csf.get_ops_switchs(self.MainOptions.total_life, self.MainOptions.in_operation)
		self.is_closed = csf.get_closed_switchs(self.MainOptions.total_life, self.MainOptions.in_operation)
		self.non_fuel_esc = self.TimeValueMoney.escalation_non
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	# @st.cache(suppress_st_warning=True)
	def AmineCaptureFacility(self):
		df = csf.create_zeros_array(self.length, rows = 12)
		
		CAPEX = self.CaptureFacilities.amine_CAPEX
		ITC = self.CaptureFacilities.amine_ITC
		MACRS = csf.calc_macrs(self.MainOptions.amine_capture_macrs, self.length)
		tax_basis_and_straight_line = csf.get_tax_basis_and_straight_line(CAPEX, ITC, self.TaxCredits.income_dep, self.MainOptions.in_operation-1)

		fan_pump_other_electricity = self.ScenarioData.op_hrs_per_yr * self.CaptureFacilities.amine_fan_pump * self.CaptureFacilities.flue_stream
		chem_consumed = self.CaptureFacilities.amine_consumables * self.CaptureFacilities.CO2_per_year * ModelConstants.to_MM
		water_consumed = self.CaptureFacilities.water_price * self.CaptureFacilities.amine_water_use * self.CaptureFacilities.flue_stream * self.ScenarioData.op_hrs_per_yr * ModelConstants.to_kilo

		df[2,:] = self.in_ops * fan_pump_other_electricity
		df[4,:] = (CAPEX * self.TimeValueMoney.escalation_non_rate) * self.TimeValueMoney.escalation * self.in_ops
		df[5,:] = (chem_consumed) * self.TimeValueMoney.escalation * self.in_ops
		df[6,:] = (water_consumed) * self.TimeValueMoney.escalation * self.in_ops
		df[8,:] = df[4:8, :].sum(axis = 0) * self.in_ops
		df[9,1:] = tax_basis_and_straight_line[0] * MACRS[:-1]
		df[10,:] = tax_basis_and_straight_line[1] * self.in_ops
		
		df[0,0] = CAPEX
		df[1,0] = ITC
		df[11,:] = csf.book_value_per_year(tax_basis_and_straight_line[0], df[10,:], self.GlobalParameters.min_book_value, self.in_ops) 
		
		df = pd.DataFrame(df, index = ['CAPEX', 'ITC',
										'Total Electricity Usage (kWhs)', 'Net Electricity Usage (kWhs)', 'Non-Fuel O&M',
										'Capture Chem Consumables', 'Water Feed', 'Purchased Electricity', 'Subtotal O&M',
										'Tax Depreciation', 'Straight Line Depreciation', 'Book Value'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache
	def CoGenFacility(self):
		df = csf.create_zeros_array(self.length, rows = 10)

		CAPEX = self.CaptureFacilities.Cogen_CAPEX
		ITC = self.CaptureFacilities.CoGen_ITC

		if CAPEX > 0:
			MACRS = csf.calc_macrs(self.MainOptions.cogen_macrs, self.length)
			tax_basis_and_straight_line = csf.get_tax_basis_and_straight_line(CAPEX, ITC, self.TaxCredits.income_dep, self.MainOptions.in_operation-1)

			elec_output = self.CaptureFacilities.aux_nameplate * self.ScenarioData.efficiency * ModelConstants.hours_per_year * ModelConstants.out_kilo
			ng_consumed = self.CaptureFacilities.CoGen_heat * ModelConstants.out_MM * ModelConstants.mmbtu_to_mcd

			df[2,:] = elec_output * self.in_ops
			df[3,:] = ng_consumed * df[2,:]
			df[4,:] = (CAPEX * self.TimeValueMoney.escalation_non_rate) * self.TimeValueMoney.escalation * self.in_ops
			df[5,:] = (df[3,:] * self.FuelPrices.ng_purchase) * self.in_ops
			df[6,:] = df[4:6, :].sum(axis = 0) * self.in_ops
			df[7,1:] = tax_basis_and_straight_line[0] * MACRS[:-1]
			df[8,:] = tax_basis_and_straight_line[1] * self.in_ops

			df[0,0] = CAPEX
			df[1,0] = ITC
			df[9,:] = csf.book_value_per_year(tax_basis_and_straight_line[0], df[8,:], self.GlobalParameters.min_book_value, self.in_ops) 
		
		df = pd.DataFrame(df, index = ['CAPEX', 'ITC',
											'CoGen Plant Output (kWhs)', 'Natural Gas Consumption (MMcfd)', 'Non-Fuel O&M', 'Fuel Cost',
											'Subtotal O&M', 'Tax Depreciation', 'Straight Line Depreciation', 'Book Value'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache
	def SteamPlantOnly(self):
		df = csf.create_zeros_array(self.length, rows = 10)

		CAPEX = self.CaptureFacilities.aux_boiler_CAPEX
		ITC = self.CaptureFacilities.aux_boiler_ITC

		if CAPEX > 0:
			MACRS = csf.calc_macrs(self.MainOptions.aux_boiler_macrs, self.length)
			tax_basis_and_straight_line = csf.get_tax_basis_and_straight_line(CAPEX, ITC, self.TaxCredits.income_dep, self.MainOptions.in_operation-1)

			elec_output = self.CaptureFacilities.aux_boiler_output

			if self.MainOptions.cogen_scenario == SelectBoxOptions.CoGen_Options[1]:
				fuel = self.FuelPrices.ng_purchase
				fuel_consumed_conversion = self.CaptureFacilities.aux_boiler_fuel * ModelConstants.mmbtu_to_mcd * ModelConstants.out_MM
			else:
				fuel = self.FuelPrices.fuel_pricing_df.loc['Powder River Coal']
				fuel_consumed_conversion = self.CaptureFacilities.aux_boiler_fuel / self.CaptureFacilities.aux_boiler_coal / self.MainOptions.tons_units
			fuel_consumed = fuel_consumed_conversion * elec_output
			fuel_consumed_conversion = self.CaptureFacilities.aux_boiler_fuel * ModelConstants.mmbtu_to_mcd * ModelConstants.to_MM

			df[2,:] = elec_output * self.in_ops
			df[3,:] = fuel_consumed * self.in_ops
			df[4,:] = (CAPEX * self.TimeValueMoney.escalation_non_rate) * self.TimeValueMoney.escalation * self.in_ops
			df[5,:] = df[3,:] * fuel
			df[6,:] = df[4:6,:].sum(axis = 0) * self.in_ops
			df[7,:1] = tax_basis_and_straight_line[0] * MACRS[:-1]
			df[8,:] = tax_basis_and_straight_line[1] * self.in_ops

			# for i in range(1, self.length):
			# 	df[2,i] = elec_output * self.in_ops[i]
			# 	df[3,i] = fuel_consumed * self.in_ops[i]
			# 	df[4,i] = (CAPEX * self.TimeValueMoney.escalation_non_rate) * self.TimeValueMoney.escalation[i] * self.in_ops[i]
			# 	df[5,i] = df[3,i] * fuel[i]
			# 	df[6,i] = df[4:6,i].sum()
			# 	df[7,i] = tax_basis_and_straight_line[0] * MACRS[i-1]
			# 	df[8,i] = tax_basis_and_straight_line[1] * self.in_ops[i]

			df[0,0] = CAPEX
			df[1,0] = ITC
			df[9,:] = csf.book_value_per_year(tax_basis_and_straight_line[0], df[8,:], self.GlobalParameters.min_book_value, self.in_ops)

		df = pd.DataFrame(df, index = ['CAPEX', 'ITC',
											'MWhs of CCS share of Plant', 'Natural Gas OR Coal Consumed (MCF OR tons/yr', 'Non-Fuel O&M',
											'Fuel Cost', 'Subtotal O&M', 'Tax Depreciation', 'Straight Line Depreciation', 'Book Value'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
	
	# @st.cache(suppress_st_warning=True)
	def CoolingTower(self):
		df = csf.create_zeros_array(self.length, rows = 11)

		CAPEX = self.CaptureFacilities.cool_tower_CAPEX
		ITC = self.CaptureFacilities.cool_tower_ITC

		if CAPEX > 0:
			MACRS = csf.calc_macrs(self.MainOptions.cooling_tower_macrs, self.length)
			tax_basis_and_straight_line = csf.get_tax_basis_and_straight_line(CAPEX, ITC, self.TaxCredits.income_dep, self.MainOptions.in_operation-1)

			elec_consumed = (4.6 * ModelConstants.out_kilo * self.ScenarioData.op_hrs_per_yr) * True
			water_cost = self.CaptureFacilities.water_price * self.CaptureFacilities.makeup_water * ModelConstants.minutes_per_year * self.ScenarioData.efficiency * ModelConstants.to_kilo

			df[2,:] = elec_consumed * self.in_ops
			df[4,:] = (CAPEX * self.TimeValueMoney.escalation_non_rate) * self.TimeValueMoney.escalation * self.in_ops
			df[5,:] = water_cost * self.TimeValueMoney.escalation * self.in_ops
			df[7,:] = df[4:7,:].sum(axis = 0) * self.in_ops
			df[8,1:] = tax_basis_and_straight_line[0] * MACRS[:-1]
			df[9,:] = tax_basis_and_straight_line[1] * self.in_ops

			# for i in range(1, self.length):
				# df[2,i] = elec_consumed * self.in_ops[i]
				# df[3,i] = df[2,i] * False
				# df[4,i] = (CAPEX * self.TimeValueMoney.escalation_non_rate) * self.TimeValueMoney.escalation[i] * self.in_ops[i]
				# df[5,i] = water_cost * self.TimeValueMoney.escalation[i] * self.in_ops[i]
				# df[6,i] = (df[3,i] * self.FuelPrices.elec_purchase[i]) * self.in_ops[i]
				# df[7,i] = df[4:7,i].sum()
				# df[8,i] = tax_basis_and_straight_line[0] * MACRS[i-1]
				# df[9,i] = tax_basis_and_straight_line[1] * self.in_ops[i]

			df[0,0] = CAPEX
			df[1,0] = ITC
			df[10,:] = csf.book_value_per_year(tax_basis_and_straight_line[0], df[9,:], self.GlobalParameters.min_book_value, self.in_ops)

		df = pd.DataFrame(df, index = ['CAPEX', 'ITC',
										'Total Electricity Usage (kWhs)', 'Net Electricity Usage (kWhs)', 'Non-Fuel O&M', 'Purchased Makeup Water',
										'Purchased Electricity', 'Subtotal O&M', 'Tax Depreciation', 'Straight Line Depreciation', 'Book Value'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	# @st.cache(suppress_st_warning=True)
	def WaterTreatmentDemineralization(self):
		df = csf.create_zeros_array(self.length, rows = 13)

		CAPEX = self.CaptureFacilities.water_demin_CAPEX
		ITC = self.CaptureFacilities.water_demin_ITC

		if CAPEX > 0:
			MACRS = csf.calc_macrs(self.MainOptions.water_demin_macrs, self.length)
			tax_basis_and_straight_line = csf.get_tax_basis_and_straight_line(CAPEX, ITC, self.TaxCredits.income_dep, self.MainOptions.in_operation-1)

			treat_elec_consumed = self.CaptureFacilities.water_per_day * ModelConstants.days_per_year * self.CaptureFacilities.water_demin_treat_use
			demin_elec_consumed = self.CaptureFacilities.demin_water_per_day * ModelConstants.days_per_year * self.CaptureFacilities.water_demin_demin_use

			chemical = self.CaptureFacilities.water_per_day * self.CaptureFacilities.water_demin_chem_cost * ModelConstants.days_per_year

			df[2,:] = treat_elec_consumed * self.in_ops
			df[3,:] = demin_elec_consumed * self.in_ops		
			df[4,:] = df[2:4,:].sum(axis = 0) * self.in_ops
			df[6,:] = (CAPEX * self.CaptureFacilities.water_demin_OM_rate) * self.TimeValueMoney.escalation * self.in_ops
			df[7,:] = chemical * self.TimeValueMoney.escalation * self.in_ops
			df[8,:] = (df[5,:] * self.FuelPrices.elec_purchase) * self.in_ops
			df[9,:] = df[6:9,:].sum(axis = 0) * self.in_ops
			df[10,1:] = tax_basis_and_straight_line[0] * MACRS[:-1]
			df[11,:] = tax_basis_and_straight_line[1] * self.in_ops

			# for i in range(1, self.length):
			# 	df[2,i] = treat_elec_consumed * self.in_ops[i]
			# 	df[3,i] = demin_elec_consumed * self.in_ops[i]		
			# 	df[4,i] = df[2:4,i].sum()
			# 	df[5,i] = df[4,i] * False
			# 	df[6,i] = (CAPEX * self.CaptureFacilities.water_demin_OM_rate) * self.TimeValueMoney.escalation[i] * self.in_ops[i]
			# 	df[7,i] = chemical * self.TimeValueMoney.escalation[i] * self.in_ops[i]
			# 	df[8,i] = (df[5,i] * self.FuelPrices.elec_purchase[i]) * self.in_ops[i]
			# 	df[9,i] = df[6:9,i].sum()
			# 	df[10,i] = tax_basis_and_straight_line[0] * MACRS[i-1]
			# 	df[11,i] = tax_basis_and_straight_line[1] * self.in_ops[i]

			df[0,0] = CAPEX
			df[1,0] = ITC
			df[12,:] = csf.book_value_per_year(tax_basis_and_straight_line[0], df[11,:], self.GlobalParameters.min_book_value, self.in_ops)
		df = pd.DataFrame(df, index = ['CAPEX', 'ITC',
										'Treatment Electricity (kWhs)', 'Demin Electricity (kWhs)', 'Total Electricity Usage (kWhs)',
										'Net Electricity Usage (kWhs)', 'Non-Fuel O&M', 'Treatment Chemicals', 'Purchased Electricity',
										'Subtotal O&M', 'Tax Depreciation', 'Straight Line Depreciation', 'Book Value'])

		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
	
	@st.cache
	def FlueGasTieIn(self):
		df = csf.create_zeros_array(self.length, rows = 7)

		CAPEX = self.CaptureFacilities.flue_gas_CAPEX
		ITC = self.CaptureFacilities.flue_gas_ITC

		if CAPEX > 0:
			MACRS = csf.calc_macrs(self.MainOptions.flue_macrs, self.length)
			tax_basis_and_straight_line = csf.get_tax_basis_and_straight_line(CAPEX, ITC, self.TaxCredits.income_dep, self.MainOptions.in_operation-1)

			df[2,:] = (CAPEX * self.CaptureFacilities.flue_gas_OM_rate) * self.TimeValueMoney.escalation * self.in_ops
			df[3,:] = df[2:3,:].sum(axis = 0) * self.in_ops
			df[4,1:] = tax_basis_and_straight_line[0] * MACRS[:-1]
			df[5,:] = tax_basis_and_straight_line[1] * self.in_ops

			# for i in range(1, self.length):
			# 	df[2,i] = (CAPEX * self.CaptureFacilities.flue_gas_OM_rate) * self.TimeValueMoney.escalation[i] * self.in_ops[i]
			# 	df[3,i] = df[2:3,i].sum()
			# 	df[4,i] = tax_basis_and_straight_line[0] * MACRS[i-1]
			# 	df[5,i] = tax_basis_and_straight_line[1] * self.in_ops[i]

			df[0,0] = CAPEX
			df[1,0] = ITC
			df[6,:] = csf.book_value_per_year(tax_basis_and_straight_line[0], df[5,:], self.GlobalParameters.min_book_value, self.in_ops)

		df = pd.DataFrame(df, index = ['CAPEX', 'ITC',
										'Non-Fuel O&M', 'Subtotal O&M', 'Tax Depreciation', 'Straight Line Depreciation', 'Book Value'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	# @st.cache(suppress_st_warning=True)
	def CompressionDehydration(self):
		df = csf.create_zeros_array(self.length, rows = 10)

		CAPEX = self.CaptureFacilities.comp_dehi_CAPEX
		ITC = self.CaptureFacilities.comp_dehi_ITC

		if CAPEX > 0:
			@st.cache(allow_output_mutation=True, suppress_st_warning=True)
			def compression_HP(comp_dehi_inlet, comp_dehi_outlet, max_capture):
				inlet_pressure = comp_dehi_inlet * 0.00689476
				critical_pressure = 7.39
				outlet_pressure = comp_dehi_outlet * 0.00689476
				comp_ratio_5_stage = (critical_pressure / inlet_pressure) ** (1/5)
				stage_1_HP = ((1000 / (24 * 3600)) * ((max_capture * 0.995 * 8.314 * 313.15) / (44.01 * 0.75)) * (1.277 / (1.277 - 1)) * ((comp_ratio_5_stage ** ((1.277-1) / 1.277)) - 1)) / 0.746
				stage_2_HP = ((1000 / (24 * 3600)) * ((max_capture * 0.985 * 8.314 * 313.15) / (44.01 * 0.75)) * (1.286 / (1.286 - 1)) * ((comp_ratio_5_stage ** ((1.286-1) / 1.286)) - 1)) / 0.746
				stage_3_HP = ((1000 / (24 * 3600)) * ((max_capture * 0.970 * 8.314 * 313.15) / (44.01 * 0.75)) * (1.309 / (1.309 - 1)) * ((comp_ratio_5_stage ** ((1.309-1) / 1.309)) - 1)) / 0.746
				stage_4_HP = ((1000 / (24 * 3600)) * ((max_capture * 0.935 * 8.314 * 313.15) / (44.01 * 0.75)) * (1.379 / (1.379 - 1)) * ((comp_ratio_5_stage ** ((1.379-1) / 1.379)) - 1)) / 0.746
				stage_5_HP = ((1000 / (24 * 3600)) * ((max_capture * 0.845 * 8.314 * 313.15) / (44.01 * 0.75)) * (1.701 / (1.701 - 1)) * ((comp_ratio_5_stage ** ((1.701-1) / 1.701)) - 1)) / 0.746

				pump_comp_HP = ((1000 * 10) / (36 * 24)) * ((max_capture * (outlet_pressure - 7.38)) / ((630 * 0.75)))
				total_compression_HP = stage_1_HP + stage_2_HP + stage_3_HP + stage_4_HP + stage_5_HP + pump_comp_HP
				return total_compression_HP
			horse_power = compression_HP(self.CaptureFacilities.comp_dehi_inlet, self.CaptureFacilities.comp_dehi_outlet, self.CaptureFacilities.max_capture)

			elec_consumed = horse_power * self.ScenarioData.op_hrs_per_yr * self.ScenarioData.efficiency

			MACRS = csf.calc_macrs(self.MainOptions.comp_dehy_macrs, self.length)
			tax_basis_and_straight_line = csf.get_tax_basis_and_straight_line(CAPEX, ITC, self.TaxCredits.income_dep, self.MainOptions.in_operation-1)

			df[2,:] = elec_consumed * self.in_ops
			df[4,:] = (CAPEX * self.TimeValueMoney.escalation_non_rate) * self.TimeValueMoney.escalation * self.in_ops
			df[5,:] = (df[3,:] * self.FuelPrices.elec_purchase) * self.in_ops
			df[6,:] = df[4:6,:].sum(axis = 0) * self.in_ops
			df[7,1:] = tax_basis_and_straight_line[0] * MACRS[:-1]
			df[8,:] = tax_basis_and_straight_line[1] * self.in_ops

			# for i in range(1, self.length):
			# 	df[2,i] = elec_consumed * self.in_ops[i]
			# 	df[3,i] = df[2,i] * False
			# 	df[4,i] = (CAPEX * self.TimeValueMoney.escalation_non_rate) * self.TimeValueMoney.escalation[i] * self.in_ops[i]
			# 	df[5,i] = (df[3,i] * self.FuelPrices.elec_purchase[i]) * self.in_ops[i]
			# 	df[6,i] = df[4:6,i].sum()
			# 	df[7,i] = tax_basis_and_straight_line[0] * MACRS[i-1]
			# 	df[8,i] = tax_basis_and_straight_line[1] * self.in_ops[i]

			df[0,0] = CAPEX
			df[1,0] = ITC
			df[9,:] = csf.book_value_per_year(tax_basis_and_straight_line[0], df[8,:], self.GlobalParameters.min_book_value, self.in_ops)

		df = pd.DataFrame(df, index = ['CAPEX', 'ITC',
										'Total Electricity Usage (kWhs)', 'Net Electricity Usage (kWhs)', 'Non-Fuel O&M', 'Purchased Electricity',
										'Subtotal O&M', 'Tax Depreciation', 'Straight Line Depreciation', 'Book Value'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #





		




