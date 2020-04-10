import streamlit as st
import pandas as pd
import math

import CarbonSafeFunctions as csf
from SideBar import ModelConstants, SelectBoxOptions

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache
def FinishFacilities(self, ElecUsage, Facility):
	self.facilities[Facility].loc['Net Electricity Usage (kWhs)', 1:] =[ElecUsage.loc['….if (Purchased), Purchase Share (%Demand)', i] * self.facilities[Facility].loc['Total Electricity Usage (kWhs)', i] for i in range(1, self.MainOptions.total_life)]
	self.facilities[Facility].loc['Purchased Electricity', 1:] = [self.facilities[Facility].loc['Net Electricity Usage (kWhs)', i] * self.FuelPrices.elec_purchase[i] for i in range(1, self.MainOptions.total_life)]
	self.facilities[Facility].loc['Subtotal O&M', 1:] = [self.facilities[Facility].loc['Subtotal O&M', i] + self.facilities[Facility].loc['Purchased Electricity', i] for i in range(1, self.MainOptions.total_life)]
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class ElecUsedByFacility:
	def __init__(self, MainOptions, facilities_dictionary, FuelPrices):
		self.MainOptions = MainOptions
		self.facilities = facilities_dictionary
		self.FuelPrices = FuelPrices

	# @st.cache(suppress_st_warning=True)
	def CalcElecUsage(self):
		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 9)

		df[0,1:] = [self.facilities['AmineCaptureFacility'].loc['Total Electricity Usage (kWhs)', i] for i in range(1, self.MainOptions.total_life)]
		df[1,1:] = [self.facilities['CompressionDehydration'].loc['Total Electricity Usage (kWhs)', i] for i in range(1, self.MainOptions.total_life)]
		df[2,1:] = [self.facilities['CoolingTower'].loc['Total Electricity Usage (kWhs)', i] for i in range(1, self.MainOptions.total_life)]
		df[3,1:] = [self.facilities['WaterTreatmentDemineralization'].loc['Total Electricity Usage (kWhs)', i] for i in range(1, self.MainOptions.total_life)]
		df[4,1:] = [self.facilities['CO2PipelineBoostersGaugesMeters'].loc['Total Electricity Usage (kWhs)', i] for i in range(1, self.MainOptions.total_life)]

		df[5,1:] = [self.facilities['CoGenFacility'].loc['CoGen Plant Output (kWhs)', i] for i in range(1, self.MainOptions.total_life)]
		df[6,1:] = [df[0:5,i].sum() for i in range(1, self.MainOptions.total_life)]
		df[7,1:] = [df[5,i] - df[6,i] for i in range(1, self.MainOptions.total_life)]
		df[8,1:] = [-df[7,i] / df[6,i] if df[7,i] < 0 else 0 for i in range(1, self.MainOptions.total_life)]
		df = pd.DataFrame(df, index = ['MHI/Amine Plant', 'Compression/Dehydration Plant', 'Cooling Tower', 'Water & Demineralization Plant',
										'CO2 Booster Stations', 'Total CoGen System Output (kWhs)', 'Total CCS System Electricity (kWhs)',
										'Net Power Sold (Purchased)', '….if (Purchased), Purchase Share (%Demand)'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	# @st.cache(suppress_st_warning=True)
	def FinishFacilitiesElec(self, ElecUsage):
		FinishFacilities(self, ElecUsage, 'AmineCaptureFacility')
		FinishFacilities(self, ElecUsage, 'CoolingTower')
		FinishFacilities(self, ElecUsage, 'WaterTreatmentDemineralization')
		FinishFacilities(self, ElecUsage, 'CompressionDehydration')
		FinishFacilities(self, ElecUsage, 'CO2PipelineBoostersGaugesMeters')






