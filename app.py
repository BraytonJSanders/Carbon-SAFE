import CarbonSafeFunctions as csf
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import math
# -------------------------------------------------------------------------------------------------------------------- #
pd.set_option('mode.chained_assignment', None)
# -------------------------------------------------------------------------------------------------------------------- #
from SideBar import SelectBoxOptions, MainOptions
from ModelScenarioData import ScenarioData
from FuelPricingData import FuelData, FuelPrices
from TimeValueMoneyData import TimeValueMoney
from MonitorSwitches import MonitorSwitchesData
from GlobalModelParameters import GlobalParameters
from CapitalStructureParameters import CapitalStructure
from RevenueReservesParameters import RevenueReserves
from PipelineSystemsParameters import PipelineSystems
from InsurancePiscLtlParameters import InsurancePiscLtl
from TaxCreditsParameters import TaxCredits
from CaptureFacilitiesParameters import CaptureFacilities
from StorageSiteParameters import StorageSite
from StorageWellsParameters import StorageWells
# -------------------------------------------------------------------------------------------------------------------- #
from CO2Parameters import CO2Parameter
from CaptureFacilitiesFinancials import CaptureFacilitiesFinancial
from PipelineSystemsFinancials import PipelineSystemsFinancial
from StorageSiteFinancials import StorageSiteFinancial
from ProjectFinancials import CapitalCost
from ElecUsedByFacilities import ElecUsedByFacility
from TechnoEconSummary import TechnoEconSummary
import DisplayResults

# streamlit run app.py

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

# @st.cache
def main_run_model(model_title, reset_message, MainOptions, ScenarioData, FuelData, FuelPrices, TimeValueMoney, MonitorSwitchesData, GlobalParameters, CapitalStructure, RevenueReserves,
					InsurancePiscLtl, CaptureFacilities, PipelineSystems, StorageSite, StorageWells):

	CaptureFacilitiesFinancials = CaptureFacilitiesFinancial(MainOptions, ScenarioData,
															FuelPrices, TimeValueMoney, MonitorSwitchesData,
															GlobalParameters, CapitalStructure, RevenueReserves,
															CaptureFacilities, TaxCredits)
	CO2Parameters = CO2Parameter(MainOptions, ScenarioData, CaptureFacilitiesFinancials, CaptureFacilities, GlobalParameters, RevenueReserves)


	PipelineSystemsFinancials = PipelineSystemsFinancial(PipelineSystems, MainOptions, ScenarioData,
															FuelPrices, TimeValueMoney, MonitorSwitchesData,
															GlobalParameters, CapitalStructure, RevenueReserves,
															CaptureFacilities, TaxCredits)
	StorageSiteFinancials = StorageSiteFinancial(StorageSite, StorageWells, MainOptions, ScenarioData,
													FuelPrices, TimeValueMoney, MonitorSwitchesData,
													GlobalParameters, CapitalStructure, RevenueReserves,
													CaptureFacilities, TaxCredits)
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	financial_dfs = {'AmineCaptureFacility': CaptureFacilitiesFinancials.AmineCaptureFacility(),
					'CoGenFacility':CaptureFacilitiesFinancials.CoGenFacility(),
					'SteamPlantOnly':CaptureFacilitiesFinancials.SteamPlantOnly(),
					'CoolingTower':CaptureFacilitiesFinancials.CoolingTower(),
					'WaterTreatmentDemineralization':CaptureFacilitiesFinancials.WaterTreatmentDemineralization(),
					'CompressionDehydration':CaptureFacilitiesFinancials.CompressionDehydration(),
					'FlueGasTieIn':CaptureFacilitiesFinancials.FlueGasTieIn(),
					'StoragePipeline': PipelineSystemsFinancials.StoragePipeline(),
					'EorSalesPipeline': PipelineSystemsFinancials.EorSalesPipeline(),
					'CO2PipelineBoostersGaugesMeters': PipelineSystemsFinancials.CO2PipelineBoostersGaugesMeters(),
					'PreInjectSite': StorageSiteFinancials.PreInjectSite(),
					'StorageOperationMonitoring': StorageSiteFinancials.StorageOperationMonitoring(StorageSiteFinancials.PreInjectSite().iloc[0 ,0], CO2Parameters.SourcePlantOperations()),
					'CO2 Post-Injection Close Monitoring': StorageSiteFinancials.PostClosure()}
	CapitalCosts = CapitalCost(financial_dfs, MainOptions, TimeValueMoney, MonitorSwitchesData, InsurancePiscLtl, CaptureFacilitiesFinancials)
	ElecUsedByFacilities = ElecUsedByFacility(MainOptions, financial_dfs, FuelPrices)

	CO2_dfs = {'CO2 Source Plant Operating Results': CO2Parameters.SourcePlantOperations(),
				'CO2 Sales & Storage Volumes': CO2Parameters.CO2SaleAndStorage(CO2Parameters.SourcePlantOperations()),
				'CO2 Tax Credits': CO2Parameters.CO2TaxCredits(TaxCredits),
				'CO2 Pricing Paths': FuelPrices.cal_CO2_price_and_green(RevenueReserves, MainOptions, TimeValueMoney),
				'CO2 Permits or Emission Credits': CO2Parameters.CO2PermitsOrEmissionCredits(),
				'Electricity Used by Capture Facilities': ElecUsedByFacilities.CalcElecUsage()}
	ElecUsedByFacilities.FinishFacilitiesElec(CO2_dfs['Electricity Used by Capture Facilities'])

	project_financial_df = {'Total Facilities CAPEX': CapitalCosts.TotalCAPEX_ITC()['Facilities CAPEX'],
							'Total ITC': CapitalCosts.TotalCAPEX_ITC()['Facilities ITC'],
							'Industrial Insurance': CapitalCosts.Insurance(CapitalCosts.TotalCAPEX_ITC()['Facilities CAPEX']),
							'Trust Funds': CapitalCosts.TrustFunds(financial_dfs['CO2 Post-Injection Close Monitoring'], CO2_dfs['CO2 Source Plant Operating Results'], CaptureFacilities),
							'Techno Economic Financial Summary': TechnoEconSummary(MainOptions, CO2_dfs['CO2 Source Plant Operating Results'], ScenarioData, CO2_dfs['Electricity Used by Capture Facilities'], CO2_dfs['CO2 Sales & Storage Volumes']).df,
							}
	project_financial_df['Revenues'] = CapitalCosts.calc_revenues(project_financial_df['Techno Economic Financial Summary'], CO2_dfs, FuelPrices)
	project_financial_df['Total Project CAPEX'] = CapitalCosts.project_CAPEX(project_financial_df['Total Facilities CAPEX'], project_financial_df['Industrial Insurance'], GlobalParameters, RevenueReserves, CapitalStructure)
	project_financial_df['Operating Costs'] = CapitalCosts.calc_OPCosts(financial_dfs, project_financial_df)
	project_financial_df['Debt Schedule'] = CapitalCosts.debt_schdule(financial_dfs, project_financial_df, CapitalStructure)
	project_financial_df['Taxes'] = CapitalCosts.calc_taxes(financial_dfs, project_financial_df, CapitalStructure)
	project_financial_df['Debt Service & Operating Reserve Account'] = CapitalCosts.debt_service(financial_dfs, project_financial_df, RevenueReserves, CapitalStructure)[0]
	project_financial_df['Debt Coverage'] = CapitalCosts.debt_service(financial_dfs, project_financial_df, RevenueReserves, CapitalStructure)[1]
	project_financial_df['Operating Income'] = CapitalCosts.calc_OPIncome(project_financial_df, CapitalStructure)
	project_financial_df['Equity Sizing'] = CapitalCosts.equity_sizing(project_financial_df, TimeValueMoney)
	project_financial_df['Total Project CAPEX'] = CapitalCosts.finish_CAPEX(project_financial_df['Total Project CAPEX'], project_financial_df)

	return [financial_dfs, project_financial_df]
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

model_title = 'UWyo - CarbonSAFE'
reset_message = 'Values Restet. Re-click checkbox to see updated values.'
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

MainOptions = MainOptions(csf.import_plant_data('Scenario_Data'))
ScenarioData = ScenarioData(csf.import_plant_data('Scenario_Data'), MainOptions)
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

csf.section_header("Fuel Pricing Options:", False)
FuelData = FuelData(reset_message)
FuelPrices = FuelPrices(FuelData, MainOptions)
FuelPrices.graph_fuel_paths(FuelData, MainOptions.in_operation)
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

csf.section_header("Model Options:")
TimeValueMoney = TimeValueMoney(MainOptions.total_life, reset_message)
MonitorSwitchesData = MonitorSwitchesData(MainOptions, reset_message)
GlobalParameters = GlobalParameters(reset_message)
CapitalStructure = CapitalStructure(reset_message)
RevenueReserves = RevenueReserves(reset_message)
InsurancePiscLtl = InsurancePiscLtl(reset_message)
TaxCredits = TaxCredits(reset_message)
CaptureFacilities = CaptureFacilities(reset_message, MainOptions, ScenarioData, GlobalParameters, TaxCredits)
PipelineSystems = PipelineSystems(reset_message, TaxCredits, CaptureFacilities, ScenarioData)
StorageSite = StorageSite(reset_message, CaptureFacilities)
StorageWells = StorageWells(reset_message, StorageSite)


in_options = [TimeValueMoney.inside, MonitorSwitchesData.inside, GlobalParameters.inside, CapitalStructure.inside,
			RevenueReserves.inside, InsurancePiscLtl.inside, TaxCredits.inside, CaptureFacilities.inside, PipelineSystems.inside,
			StorageSite.inside, StorageWells.inside]

pass_checkbox = False

if sum(in_options) == 0:
	csf.section_header('*Check Box to Run Model*', line_above = False)
	if st.checkbox('Run Model')| pass_checkbox:
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

		results = main_run_model(model_title, reset_message, MainOptions, ScenarioData, FuelData, FuelPrices, TimeValueMoney, MonitorSwitchesData, GlobalParameters, CapitalStructure, RevenueReserves,
											InsurancePiscLtl, CaptureFacilities, PipelineSystems, StorageSite, StorageWells)
		financial_dfs = results[0]
		project_financial_df = results[1]

		# financial_dfs['CO2 Post-Injection Close Monitoring']
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
		st.success('Model Successful!')
		csf.main_body_divider()
		csf.main_body_divider()
		csf.section_header('Model Results', line_above = False)
		DisplayResults.display_dataframes(financial_dfs, project_financial_df)
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

		st.subheader("Cost Summary:")
		st.text('[In Millions of USD]')
		cost_summary = DisplayResults.create_cost_summary(financial_dfs, project_financial_df, CaptureFacilities)
		st.dataframe(cost_summary)

		DisplayResults.individual_cost_summary(cost_summary)
		multi_dipsplay_df = DisplayResults.create_summary_df_for_graph(MainOptions, financial_dfs, project_financial_df)
		DisplayResults.multiple_display_graph(multi_dipsplay_df)

	else:
		csf.main_body_divider()
else:
	pass
st.text(datetime.today().strftime('%A - %B %d, %Y'))


# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# st.dataframe(CO2Parameters.CO2TaxCredits(TaxCredits))
# st.dataframe(financial_dfs['AmineCaptureFacility'])


