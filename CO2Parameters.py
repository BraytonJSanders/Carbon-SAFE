import streamlit as st
import pandas as pd
import numpy as np

from datetime import datetime

import CarbonSafeFunctions as csf
from SideBar import ModelConstants, SelectBoxOptions

@st.cache
def complex_45Q(self, df, TaxCredits):

	CO2_year_one = TaxCredits.CO2_one
	CO2_year_end = TaxCredits.CO2_end

	year_one = TaxCredits.saline_one
	year_end = TaxCredits.saline_end
	r = 1.5 / 100
	begin = self.MainOptions.year_zero - 1

	year_count = self.MainOptions.tax_45Q_claimed
	applicable_year_last = self.MainOptions.tax_45Q_year_last + year_count + 1

	increment_1 = (year_end - year_one) / (self.MainOptions.tax_45Q_year_last - self.MainOptions.tax_45Q_year_one)
	increment_2 = (CO2_year_end - CO2_year_one) / (self.MainOptions.tax_45Q_year_last - self.MainOptions.tax_45Q_year_one)

	for i in range(1, self.MainOptions.total_life):
		if (begin + i) < ((begin + i) + year_count):
			if (begin + i) > applicable_year_last:
				df[0,i] = 0
				df[1,i] = 0
			elif (begin + i) < self.MainOptions.tax_45Q_year_one:
				df[0,i] = 0
				df[1,i] = 0
			elif (begin + i) <= self.MainOptions.tax_45Q_year_last:
				df[0,i] = ((begin + i) - self.MainOptions.tax_45Q_year_one) * increment_1 + year_one
				df[1,i] = ((begin + i) - self.MainOptions.tax_45Q_year_one) * increment_2 + year_one
			else:
				df[0,i] = year_end * ((1 + r) ** ((begin + i) - self.MainOptions.tax_45Q_year_last))
				df[1,i] = CO2_year_end * ((1 + r) ** ((begin + i) - self.MainOptions.tax_45Q_year_last))
		else: 
			df[0,i] = 0
			df[1,i] = 0
	return df

@st.cache
def simple_45Q(self, df, TaxCredits):

	CO2_year_one = TaxCredits.CO2_one
	CO2_year_end = TaxCredits.CO2_end

	year_one = TaxCredits.saline_one
	year_end = TaxCredits.saline_end
	r = 1.5 / 100
	current = int(datetime.today().year)
	begin = self.MainOptions.year_zero - 1

	df[0,1:] = [(year_one * (1 + r) ** ((begin + i) - current)) for i in range(1, self.MainOptions.total_life)]
	df[1,1:] = [(CO2_year_one * (1 + r) ** ((begin + i) - current)) for i in range(1, self.MainOptions.total_life)]

	return df


@st.cache(suppress_st_warning=True)
def CO2SalesShares(CO2_share, CO2_share_constant, length):
	if CO2_share == SelectBoxOptions.Share_CO2_to_EOR_Options[0]: # Constant Share
		CO2_path = np.full(length, CO2_share_constant)
	else: # Custom Share
		CO2_path = np.full(length, .9)
		tend = np.array([0,.1,.3,.5,.7,.9])
		CO2_path[:len(tend)] = tend
	return CO2_path

class CO2Parameter:
	def __init__(self, MainOptions, ScenarioData, CaptureFacilitiesFinancials, CaptureFacilities, GlobalParameters, RevenueReserves):
		self.MainOptions = MainOptions
		self.ScenarioData = ScenarioData
		self.CaptureFacilitiesFinancials = CaptureFacilitiesFinancials
		self.CaptureFacilities = CaptureFacilities
		self.cap_effic = GlobalParameters.cap_eff
		self.RevenueReserves = RevenueReserves

	@st.cache(suppress_st_warning=True)
	def SourcePlantOperations(self):
		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 6)

		elec_output = self.ScenarioData.name_plate * self.ScenarioData.op_hrs_per_yr
		CO2_produced = self.ScenarioData.CO2_lbs_MW / self.MainOptions.tons_units
		flue_stream_share = self.CaptureFacilities.flue_stream / self.ScenarioData.name_plate

		df[0,1:] = [elec_output * self.CaptureFacilitiesFinancials.in_ops[i] for i in range(1, self.MainOptions.total_life)]
		df[1,1:] = [CO2_produced * df[0,i] * self.CaptureFacilitiesFinancials.in_ops[i] for i in range(1, self.MainOptions.total_life)]
		df[2,1:] = [df[0,i] * flue_stream_share * self.CaptureFacilitiesFinancials.in_ops[i] for i in range(1, self.MainOptions.total_life)]
		df[3,1:] = [df[1,i] * flue_stream_share * self.CaptureFacilitiesFinancials.in_ops[i] for i in range(1, self.MainOptions.total_life)]
		df[4,1:] = [df[3,i] * self.cap_effic for i in range(1, self.MainOptions.total_life)]
		for i in range(1, self.MainOptions.total_life):
			df[5,i] = df[5,i-1] + df[4,i] / 1000000
		df = pd.DataFrame(df, index = ['Total Plant Output (MWhs/year)', 'CO2 Produced (tCO2/year)', 'Flue Stream, Share of Plant (MWhs/year)', 'Flue CO2 Content (tCO2/year)',
										'CO2 Captured (tCO2/year)', 'Cumulative'])
		return df

	@st.cache(suppress_st_warning=True)
	def CO2SaleAndStorage(self, SourcePlantOperations):
		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 4)

		CO2SalesShare = CO2SalesShares(self.MainOptions.CO2_share, self.MainOptions.CO2_share_constant, self.MainOptions.total_life)

		df[0,1:] = [CO2SalesShare[i] * SourcePlantOperations.loc['CO2 Captured (tCO2/year)', i] for i in range(1, self.MainOptions.total_life)]
		df[2,1:] = [SourcePlantOperations.loc['CO2 Captured (tCO2/year)', i] - df[0,i] for i in range(1, self.MainOptions.total_life)]

		for i in range(1, self.MainOptions.total_life):
			df[1,i] = df[0,i] / 1000000 + df[1,i-1]
			df[3,i] = df[2,i] / 1000000 + df[3,i-1]

		df = pd.DataFrame(df, index = ['Sales, CO2 Sold to EOR (tCO2/year)', 'Cumulative Sales (MtCO2)', 'Storage, CO2 Sequestered (tCO2/year)', 'Cumulative Storage (MtCO2)'])
		return df

	@st.cache(suppress_st_warning=True)
	def CO2PermitsOrEmissionCredits(self):
		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 2)

		EOR = self.RevenueReserves.tradeable_value
		Storage = self.RevenueReserves.tradeable_value * 0.5

		escalation = self.RevenueReserves.tradeable_escalation

		df[0,1:] = [(EOR * ((1 + escalation) ** (i - 1))) for i in range(1, self.MainOptions.total_life)]
		df[1,1:] = [(Storage * ((1 + escalation) ** (i - 1))) for i in range(1, self.MainOptions.total_life)]

		df = pd.DataFrame(df, index = ['EOR - Tradable Carbon Offset', 'Storage - Tradable Carbon Offset'])
		return df

	@st.cache(suppress_st_warning=True)
	def CO2TaxCredits(self, TaxCredits):
		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 2)
			# Tax_45Q_Options = ['Status Quo 45Q', '45Q w/No Cap', '"Future Act" 45Q', 'No 45Q/Tax Credits']
		if self.MainOptions.tax_45Q == SelectBoxOptions.Tax_45Q_Options[0]: # Status Quo 45Q
			df = simple_45Q(self, df, TaxCredits)
			df[0,1:] = [(1 if (self.MainOptions.year_zero - 1 + i) < self.MainOptions.tax_45Q_status_quo_max_date else 0) * df[0,i] for i in range(1, self.MainOptions.total_life)]
			df[1,1:] = [(1 if (self.MainOptions.year_zero - 1 + i) < self.MainOptions.tax_45Q_status_quo_max_date else 0) * df[1,i] for i in range(1, self.MainOptions.total_life)]
		elif self.MainOptions.tax_45Q == SelectBoxOptions.Tax_45Q_Options[1]: # '45Q w/No Cap',
			df = simple_45Q(self, df, TaxCredits)
		elif self.MainOptions.tax_45Q == SelectBoxOptions.Tax_45Q_Options[2]: # Future Act" 45Q
			df = complex_45Q(self, df, TaxCredits)

		df = pd.DataFrame(df, index = ['Storage Value ($/tCO2)', 'EOR Value ($/tCO2)'])
		return df







