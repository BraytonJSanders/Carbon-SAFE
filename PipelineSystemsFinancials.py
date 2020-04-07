import streamlit as st
import pandas as pd
import numpy as np
import math

from datetime import datetime

import CarbonSafeFunctions as csf
from SideBar import ModelConstants, SelectBoxOptions
from CaptureFacilitiesFinancials import CaptureFacilitiesFinancial

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache(suppress_st_warning=True)
def pipeline_cost_estimate(PipelineSystems, FuelPrices, ScenarioData):#plant_scenario_data, flue_gas_source, main_fuel_pricing_df, length_data):
	df = pd.read_csv('data/pipeline/pipeline_cost_estimate_data.csv', index_col = 0)
	
	pipe_sizes = pd.DataFrame([[36,35.16,56.46],
								[30,19.69,35.16],
								[24,12.26,19.69],
								[20,6.86,12.26],
								[16,3.25,6.86],
								[12,1.16,3.25],
								[8,0.68,1.16],
								[6,0.19,0.68],
								[4,0,0.29]], columns = ['diameter', 'lower_tonnes', 'upper_tonnes'])
	pipe_sizes.set_index('diameter', inplace = True)

	pipe_sizes['average_tonnes'] = [pipe_sizes.iloc[i][pipe_sizes.columns[0:2]].mean() for i in range(len(pipe_sizes.index))]
	pipe_sizes['lower_rate'] = [pipe_sizes.iloc[i]['lower_tonnes'] * ModelConstants.out_kilo * 19.25 / ModelConstants.days_per_year for i in range(len(pipe_sizes.index))]
	pipe_sizes['upper_rate'] = [pipe_sizes.iloc[i]['upper_tonnes'] * ModelConstants.out_kilo * 19.25 / ModelConstants.days_per_year for i in range(len(pipe_sizes.index))]
	pipe_sizes['average_rate'] = [pipe_sizes.iloc[i][['lower_rate', 'upper_rate']].mean() for i in range(len(pipe_sizes.index))]

	min_val = 100000
	for value in pipe_sizes['average_rate']:
		if (min_val > value) and (value > PipelineSystems.pipe_capacity):
			min_val = value
	pipeline_diameter = (pipe_sizes[pipe_sizes['average_rate'] == min_val].index)[0]

	year = int(datetime.now().year)

	wti_crude = FuelPrices.loc['WTI Crude', 0]

	storage_milage = ScenarioData.storage_pipe
	EOR_milage = ScenarioData.sales_pipe

	for n in range(0,5):
		if n < 2:
			base = df.loc['PPI OG Mfg']['Base Value 2']
		elif n >= 2 and n < 4:
			base = df.loc['Nelson-Farrar Labor']['Base Value 2']
		else:
			base = df.loc['CPI_LFE']['Base Value 2']

		data = [2,3,4,5,6,7,8,9,10,11,12]

		for i in range(2, 13):
			data[i-2] = df.iloc[i][df.columns[n]] * df.iloc[i]['Assumed']

		df.loc['Storage Site Line'][df.columns[n]] =  base * math.exp(sum(data) + year * df.loc['year'][df.columns[n]] + df.loc['cons'][df.columns[n]]) * (storage_milage ** df.loc['L'][df.columns[n]]) * (pipeline_diameter ** df.loc['D'][df.columns[n]]) * (wti_crude ** df.loc['wti'][df.columns[n]])
		df.loc['EOR Sales Line'][df.columns[n]] =  base * math.exp(sum(data) + year * df.loc['year'][df.columns[n]] + df.loc['cons'][df.columns[n]]) * (EOR_milage ** df.loc['L'][df.columns[n]]) * (pipeline_diameter ** df.loc['D'][df.columns[n]]) * (wti_crude ** df.loc['wti'][df.columns[n]])

	df.loc['Storage Site Line']['Assumed'] = df.loc['Storage Site Line'][1:5].sum()
	df.loc['EOR Sales Line']['Assumed'] = df.loc['EOR Sales Line'][1:5].sum()

	storage_CAPEX = (df.loc['Storage Site Line']['Total'] + df.loc['Storage Site Line']['Assumed']) / 2 / storage_milage / pipeline_diameter
	EOR_CAPEX = (df.loc['EOR Sales Line']['Total'] + df.loc['EOR Sales Line']['Assumed']) / 2 / EOR_milage / pipeline_diameter
	
	return {"DataFrame": df,
			'Storage CAPEX': storage_CAPEX,
			'EOR CAPEX': EOR_CAPEX,
			'Pipe Diameter': pipeline_diameter}
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache(suppress_st_warning=True)
def capital_costs_pressure_boosting_pump(CaptureFacilities, PipelineSystems):
	ground_temp = ModelConstants.to_K(45.6)

	Kg_per_second_CO2 = CaptureFacilities.CO2_per_year * 1.25 * 1000000000 / (ModelConstants.hours_per_year * 3600)
	
	inlet = 1400 * ModelConstants.psi_to_Mpa
	outlet = 2300 * ModelConstants.psi_to_Mpa
	average = (inlet + outlet) / 2

	pump_efficiency = 0.75
	CO2_density = (1000000 * average) / (287.058 * ground_temp) * 6.177
	KW_rating_pump =  Kg_per_second_CO2 * (outlet - inlet) * ModelConstants.out_kilo / (CO2_density * pump_efficiency)
	return (PipelineSystems.fixed_CAPEX + KW_rating_pump * 1500) # CAPEX_station
	
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class PipelineSystemsFinancial(CaptureFacilitiesFinancial):
	def __init__(self, PipelineSystems, *args, **kwargs):
		super(PipelineSystemsFinancial, self).__init__(*args, **kwargs)
		self.PipelineSystems = PipelineSystems
		self.pipeline_cost_data = pipeline_cost_estimate(self.PipelineSystems, self.FuelPrices.fuel_pricing_df, self.ScenarioData)

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
	
	@st.cache(suppress_st_warning=True)
	def StoragePipeline(self):
		df = csf.create_zeros_array(self.length, rows = 7)

		CAPEX = self.pipeline_cost_data['Storage CAPEX'] * self.pipeline_cost_data['Pipe Diameter'] * self.ScenarioData.storage_pipe
		ITC = csf.calc_federal_ITC(CAPEX, self.TaxCredits.ITC_CAPEX, self.TaxCredits.invest_tax_cred)
		

		MACRS = csf.calc_macrs(self.MainOptions.storage_pipe_macrs, self.length)
		tax_basis_and_straight_line = csf.get_tax_basis_and_straight_line(CAPEX, ITC, self.TaxCredits.income_dep, self.MainOptions.in_operation-1)

		non_fuel_OM = self.PipelineSystems.CCS_pipe * self.ScenarioData.storage_pipe
		
		df[0,0] = CAPEX
		df[1,0] = ITC
		df[2,1:] = [(non_fuel_OM * self.TimeValueMoney.escalation[i] * self.in_ops[i]) for i in range(1, self.length)]
		df[3,1:] = df[2,1:]
		df[4,1:] = [tax_basis_and_straight_line[0] * MACRS[i-1] for i in range(1, self.length)]
		df[5,1:] = [tax_basis_and_straight_line[1] * self.in_ops[i] for i in range(1, self.length)]
		df[6,:] = csf.book_value_per_year(tax_basis_and_straight_line[0], df[5,:], self.GlobalParameters.min_book_value, self.in_ops) 

		df = pd.DataFrame(df, index = ['CAPEX', 'ITC',
										'Non-Fuel O&M', 'Subtotal O&M',
										'Tax Depreciation', 'Straight Line Depreciation', 'Book Value'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
	
	@st.cache(suppress_st_warning=True)
	def EorSalesPipeline(self):
		df = csf.create_zeros_array(self.length, rows = 7)

		CAPEX = self.pipeline_cost_data['EOR CAPEX'] * self.pipeline_cost_data['Pipe Diameter'] * self.ScenarioData.sales_pipe
		ITC = csf.calc_federal_ITC(CAPEX, self.TaxCredits.ITC_CAPEX, self.TaxCredits.invest_tax_cred)

		MACRS = csf.calc_macrs(self.MainOptions.eor_pipe_macrs, self.length)
		tax_basis_and_straight_line = csf.get_tax_basis_and_straight_line(CAPEX, ITC, self.TaxCredits.income_dep, self.MainOptions.in_operation-1)

		non_fuel_OM = self.PipelineSystems.EOR_pipe * self.ScenarioData.sales_pipe

		df[0,0] = CAPEX
		df[1,0] = ITC
		df[2,1:] = [(non_fuel_OM * self.TimeValueMoney.escalation[i] * self.in_ops[i]) for i in range(1, self.length)]
		df[3,1:] = df[2,1:]
		df[4,1:] = [tax_basis_and_straight_line[0] * MACRS[i-1] for i in range(1, self.length)]
		df[5,1:] = [tax_basis_and_straight_line[1] * self.in_ops[i] for i in range(1, self.length)]
		df[6,:] = csf.book_value_per_year(tax_basis_and_straight_line[0], df[5,:], self.GlobalParameters.min_book_value, self.in_ops) 

		df = pd.DataFrame(df, index = ['CAPEX', 'ITC',
								'Non-Fuel O&M', 'Subtotal O&M',
								'Tax Depreciation', 'Straight Line Depreciation', 'Book Value'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
	
	@st.cache(suppress_st_warning=True)
	def CO2PipelineBoostersGaugesMeters(self):
		df = csf.create_zeros_array(self.length, rows = 10)

		CAPEX = (capital_costs_pressure_boosting_pump(self.CaptureFacilities, self.PipelineSystems) * self.PipelineSystems.count_boosters) + (self.PipelineSystems.meters_gauges * self.PipelineSystems.count_meters)
		ITC = csf.calc_federal_ITC(CAPEX, self.TaxCredits.ITC_CAPEX, self.TaxCredits.invest_tax_cred)


		MACRS = csf.calc_macrs(self.MainOptions.meters_boosters_macrs, self.length)
		tax_basis_and_straight_line = csf.get_tax_basis_and_straight_line(CAPEX, ITC, self.TaxCredits.income_dep, self.MainOptions.in_operation-1)

		elec_consumed = self.PipelineSystems.count_boosters * capital_costs_pressure_boosting_pump(self.CaptureFacilities, self.PipelineSystems) * self.ScenarioData.op_hrs_per_yr

		df[0,0] = CAPEX
		df[1,0] = ITC
		df[2,1:] = [elec_consumed * self.in_ops[i] for i in range(1, self.length)]
		df[3,1:] = [df[2,i] * False for i in range(1, self.length)]
		df[4,1:] = [df[3,i] * self.FuelPrices.elec_purchase[i] * self.in_ops[i] for i in range(1, self.length)]
		df[5,1:] = [CAPEX * self.PipelineSystems.meters_gauges_OM_rate * self.TimeValueMoney.escalation[i] * self.in_ops[i] for i in range(1, self.length)]
		df[6,1:] = [df[4:6,i].sum() for i in range(1, self.length)]
		df[7,1:] = [tax_basis_and_straight_line[0] * MACRS[i-1] for i in range(1, self.length)]
		df[8,1:] = [tax_basis_and_straight_line[1] * self.in_ops[i] for i in range(1, self.length)]
		df[9,:] = csf.book_value_per_year(tax_basis_and_straight_line[0], df[8,:], self.GlobalParameters.min_book_value, self.in_ops) 

		df = pd.DataFrame(df, index = ['CAPEX', 'ITC',
										'Total Electricity Usage (kWhs)', 'Net Electricity Usage (kWhs)', 'Purchased Electricity',
										'Non-Power O&M', 'Subtotal O&M', 'Tax Depreciation', 'Straight Line Depreciation', 'Book Value'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

		


