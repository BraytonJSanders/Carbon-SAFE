import streamlit as st
import pandas as pd
import numpy as np

import CarbonSafeFunctions as csf
# from SideBar import ModelConstants, SelectBoxOptions


@st.cache(suppress_st_warning=True)
def calc_value(MainOptions, SourcePlantOperations, ScenarioData, ElecUsedByFacilities, CO2SaleAndStorage):
	df = csf.create_zeros_array(MainOptions.total_life, rows = 15)

	lbs_MHw = ScenarioData.CO2_lbs_MW
	lbs_tCO2 = MainOptions.tons_units
	
	df[0,1:] = [SourcePlantOperations.loc['Total Plant Output (MWhs/year)', i] for i in range(1, MainOptions.total_life)]
	df[1,1:] = [df[0,i] * lbs_MHw / lbs_tCO2 for i in range(1, MainOptions.total_life)]
	df[2,1:] = [max(0, ElecUsedByFacilities.loc['Net Power Sold (Purchased)', i]) / 1000 for i in range(1, MainOptions.total_life)]
	df[3,1:] = [df[2,i] * lbs_MHw / lbs_tCO2 * 0.5 for i in range(1, MainOptions.total_life)]
	df[4,1:] = [df[0,i] + df[2,i] for i in range(1, MainOptions.total_life)]
	df[5,1:] = [df[1,i] + df[3,i] for i in range(1, MainOptions.total_life)]
	df[6,1:] = [SourcePlantOperations.loc['CO2 Captured (tCO2/year)', i] for i in range(1, MainOptions.total_life)]
	df[7,1:] = [round((df[6,i] / df[5,i]) * 100,1) if df[5,i] > 0 else 0 for i in range(1, MainOptions.total_life)]
	df[8,1:] = [CO2SaleAndStorage.loc['Sales, CO2 Sold to EOR (tCO2/year)', i] for i in range(1, MainOptions.total_life)]
	df[9,1:] = [round((df[8,i] / df[6,i]) * 100,1) if df[6,i] > 0 else 0 for i in range(1, MainOptions.total_life)]
	df[10,1:] = [CO2SaleAndStorage.loc['Storage, CO2 Sequestered (tCO2/year)', i] for i in range(1, MainOptions.total_life)]
	df[11,1:] = [round((df[10,i] / df[6,i]) * 100,1) if df[6,i] > 0 else 0 for i in range(1, MainOptions.total_life)]
	df[12,1:] = [df[4,i] * df[7,i] / 100 * df[9,i] / 100 for i in range(1, MainOptions.total_life)]
	df[13,1:] = [df[4,i] * df[7,i] / 100 * df[11,i] / 100 for i in range(1, MainOptions.total_life)]
	df[14,1:] = [df[12:14,i].sum() for i in range(1, MainOptions.total_life)]

	df = pd.DataFrame(df, index = ['Total MWhs of Source Plant', 'Total Source CO2 Produced', 'Total MWhs of CoGen Plant', 'Total CoGen CO2 Produced',
									'TOTAL MWhs Produced', 'TOTAL CO2 Produced', 'Total Captured CO2 from Project (tCO2)', '% of Total',
									'Sold to EOR (tCO2)', 'EOR % of Total', 'Saline Storage (tCO2)', 'Storage % of Total',
									'Green "EOR" Electrons (MWhs)', 'Green "Storage" Electrons (MWhs)', 'Total Green Electrons'])
	return df


class TechnoEconSummary:
	def __init__(self, MainOptions, SourcePlantOperations, ScenarioData, ElecUsedByFacilities, CO2SaleAndStorage):
		self.df = calc_value(MainOptions, SourcePlantOperations, ScenarioData, ElecUsedByFacilities, CO2SaleAndStorage)
	





