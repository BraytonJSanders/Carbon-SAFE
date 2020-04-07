import streamlit as st
import pandas as pd
import numpy as np
from math import ceil

import CarbonSafeFunctions as csf
from SideBar import ModelConstants, SelectBoxOptions

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class CapitalCost:
	def __init__(self, dictionary, MainOptions, TimeValueMoney, MonitorSwitchesData, InsurancePiscLtl, CaptureFacilitiesFinancials):
		self.dictionary = dictionary
		self.MainOptions = MainOptions
		self.TimeValueMoney = TimeValueMoney
		self.MonitorSwitchesData = MonitorSwitchesData
		self.InsurancePiscLtl = InsurancePiscLtl
		self.CaptureFacilitiesFinancials = CaptureFacilitiesFinancials
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache(suppress_st_warning=True)
	def TotalCAPEX_ITC(self):
		CAPEX_list = []
		ITC_list = []
		for facility, df in self.dictionary.items():
			CAPEX_list.append(df.iloc[0,0])
			ITC_list.append(df.iloc[1,0])

		CAPEX_list = pd.DataFrame(CAPEX_list, index = self.dictionary.keys(), columns = ['CAPEX'])
		ITC_list = pd.DataFrame(ITC_list, index = self.dictionary.keys(), columns = ['Investment Tax Credit'])

		return {'Facilities CAPEX': CAPEX_list,
				'Facilities ITC': ITC_list}
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache(suppress_st_warning=True)
	def Insurance(self, TOTAL_facilities_CAPEX):
		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 2)

		premium = self.InsurancePiscLtl.adjusted_premium * sum(TOTAL_facilities_CAPEX[TOTAL_facilities_CAPEX.columns[0]])

		df[0,0] = self.InsurancePiscLtl.underwrite * sum(TOTAL_facilities_CAPEX[TOTAL_facilities_CAPEX.columns[0]])
		df[1,1:] = [premium * self.TimeValueMoney.escalation[i] if i <= (self.MainOptions.in_operation-2) else 0 for i in range(self.MainOptions.total_life-1)]

		df = pd.DataFrame(df, index = ['Underwrite Insurance Fee', 'Annual Premium'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache(suppress_st_warning=True)
	def TrustFunds(self, post_closure_df, SourcePlantOperations, CaptureFacilities):
		df_PSIC = csf.create_zeros_array(self.MainOptions.total_life, rows = 4)

		PISC_rate = self.InsurancePiscLtl.PISC_return
		pv = np.pv(PISC_rate, self.MainOptions.post_closer, - post_closure_df.loc['Total PISC & MVA CAPEX+OPEX'].sum() * (1 + self.InsurancePiscLtl.PISC_cont) / 1000000 / self.MainOptions.post_closer,0)
		
		pmt = np.pmt(PISC_rate, self.MainOptions.in_operation-1, 0, -pv * 1000000)
	
		df_PSIC[0,1:] = [pmt * self.CaptureFacilitiesFinancials.in_ops[i] for i in range(1, self.MainOptions.total_life)]
		df_PSIC[2,1:] = [- post_closure_df.loc['Total PISC & MVA CAPEX+OPEX', i] for i in range(1, self.MainOptions.total_life)]

		for i in range(1, self.MainOptions.total_life):
			df_PSIC[1,i] = df_PSIC[3,i-1] * PISC_rate
			df_PSIC[3,i] = df_PSIC[0:3,i].sum() + df_PSIC[3,i-1]
		df_PSIC = pd.DataFrame(df_PSIC, index = ['Payments to PISC Trust', 'Interest Earned', 'Less PISC Expenses', 'Cumulative Value ($MM)'])
#---------------------------------------------------------------------------------------- #

		df_LTL = csf.create_zeros_array(self.MainOptions.total_life, rows = 3)

		LTL_rate = self.InsurancePiscLtl.LTL_return
		
		fv_loss = -np.fv(self.InsurancePiscLtl.LTL_inflation, self.MainOptions.total_life-1, 0,self.InsurancePiscLtl.max_loss_res * (1 + self.InsurancePiscLtl.LTL_cont))
		pv_loss = -np.pv(LTL_rate, self.MainOptions.post_closer, 0, fv_loss*self.InsurancePiscLtl.chance_event)
		pmt = -np.pmt(LTL_rate, self.MainOptions.in_operation-1, 0, pv_loss)
		fee = pmt / CaptureFacilities.CO2_per_year
		pmt_trust = SourcePlantOperations.loc['CO2 Captured (tCO2/year)', 1] * fee

		df_LTL[0,1:] = [pmt_trust * self.CaptureFacilitiesFinancials.in_ops[i] for i in range(1, self.MainOptions.total_life)]

		for i in range(1, self.MainOptions.total_life):
			df_LTL[1,i] = df_LTL[2,i-1] * LTL_rate
			df_LTL[2,i] = df_LTL[0:2,i].sum() + df_LTL[2,i-1]
		df_LTL = pd.DataFrame(df_LTL, index = ['Payments to LTL Trust', 'Interest Earned', 'Cumulative Value ($MM)'])

		return {'PSIC Trust': df_PSIC,
				'LTL Trust': df_LTL} 
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache(suppress_st_warning=True)
	def calc_revenues(self, TechnoEconSummary, CO2_dfs, FuelPrices):
		CO2_Pricing_Paths = CO2_dfs['CO2 Pricing Paths']
		ElecUsedByFacilities = CO2_dfs['Electricity Used by Capture Facilities']
		CO2PermitsOrEmissionCredits = CO2_dfs['CO2 Permits or Emission Credits']
		CO2TaxCredits = CO2_dfs['CO2 Tax Credits']

		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 9)

		mcf_per_tCO2 = (17.4825175 * self.MainOptions.tons_units / 2000)

		if self.MainOptions.realize == SelectBoxOptions.Realize_Offset_Green_Elec[0]:
			is_green_elec = 1
			is_tradable = 1
		elif self.MainOptions.realize_one == SelectBoxOptions.no_What_Applies[0]:
			is_green_elec = 0
			is_tradable = 1
		else:
			is_green_elec = 1
			is_tradable = 0

		df[0,1:] = [TechnoEconSummary.loc['Sold to EOR (tCO2)', i] * CO2_Pricing_Paths.loc['CO2-EOR Price ($/Mcf)', i] * mcf_per_tCO2  for i in range(1, self.MainOptions.total_life)]
		df[1,1:] = [max(ElecUsedByFacilities.loc['Net Power Sold (Purchased)', i] * FuelPrices.elec_sold[i], 0) / 1000 for i in range(1, self.MainOptions.total_life)]
		df[2,1:] = [CO2_Pricing_Paths.loc['EOR Carbon "Green" Premium ($/MWh)', i] * TechnoEconSummary.loc['Green "EOR" Electrons (MWhs)', i] * is_green_elec for i in range(1, self.MainOptions.total_life)]
		df[3,1:] = [CO2_Pricing_Paths.loc['Sequestration "Green" Premium ($/MWh)', i] * TechnoEconSummary.loc['Green "Storage" Electrons (MWhs)', i] * is_green_elec for i in range(1, self.MainOptions.total_life)]
		df[4,1:] = [TechnoEconSummary.loc['Sold to EOR (tCO2)',i] * CO2PermitsOrEmissionCredits.loc['EOR - Tradable Carbon Offset', i] * is_tradable for i in range(1, self.MainOptions.total_life)]
		df[5,1:] = [TechnoEconSummary.loc['Saline Storage (tCO2)',i] * CO2PermitsOrEmissionCredits.loc['EOR - Tradable Carbon Offset', i] * is_tradable for i in range(1, self.MainOptions.total_life)]
		df[6,1:] = [CO2TaxCredits.loc['Storage Value ($/tCO2)', i] * TechnoEconSummary.loc['Saline Storage (tCO2)',i] for i in range(1, self.MainOptions.total_life)]
		df[7,1:] = [CO2TaxCredits.loc['EOR Value ($/tCO2)', i] * TechnoEconSummary.loc['Sold to EOR (tCO2)',i] for i in range(1, self.MainOptions.total_life)]
		df[8,1:] = [df[0:6,i].sum() for i in range(1, self.MainOptions.total_life)]

		df = pd.DataFrame(df, index = ['CO2 Sold to EOR', 'Excess CoGen Power Sold', 'Green "EOR" Electron Sales (to CA)', 'Green "Storage" Electron Sales (to CA)',
										'"EOR" Tradable Offsets', '"Storage" Tradable Offsets',
										'45Q Storage Credits', '45Q EOR Credits', 'Total Direct Revenues'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	# @st.cache(suppress_st_warning=True) # DONT CASHE!
	def project_CAPEX(self, facilities_CAPEX, Insurance, GlobalParameters, RevenueReserves, CapitalStructure):
		cap_facilities_CAPEX = sum(facilities_CAPEX[facilities_CAPEX.columns[0]])

		insurance = Insurance.iloc[0, 0]
		owner_cost = cap_facilities_CAPEX * GlobalParameters.owner_CAPEX + insurance
		debt_reserve = 69

		DOE_grant = RevenueReserves.grant * 1000000
		DOE_share = RevenueReserves.other_share * 1000000

		CAPEX = cap_facilities_CAPEX + insurance + owner_cost - DOE_grant - DOE_share # + debt_reserve

		df = pd.DataFrame([[insurance], [owner_cost], [debt_reserve], [DOE_grant], [DOE_share], [CAPEX]], index = ['Insurance Underwriting', "Provision for Owner's Costs", 'Debt Reserve & Working Capital', 'DOE Grant for Site Characterization',
																									'Other DOE Cost Sharing', 'Total CAPEX'], columns = [facilities_CAPEX.columns[0]])
		df = pd.concat([facilities_CAPEX, df], axis = 0)
		return df

	# @st.cache(suppress_st_warning=True) # DONT CASHE!
	def finish_CAPEX(self, CAPEX, project_financial_df):
		CAPEX.loc['Debt Reserve & Working Capital'] = abs(project_financial_df['Debt Service & Operating Reserve Account'].loc['Ending Balance', 0])
		CAPEX.loc['Total CAPEX'] = CAPEX.loc['Total CAPEX'] + CAPEX.loc['Debt Reserve & Working Capital']
		return CAPEX

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache(suppress_st_warning=True)
	def calc_OPCosts(self, financial_dfs, project_financial_df):
		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 27)

		df[0,1:] = [financial_dfs['AmineCaptureFacility'].loc['Subtotal O&M', i] + financial_dfs['FlueGasTieIn'].loc['Subtotal O&M', i] for i in range(1, self.MainOptions.total_life)]
		df[1,:] = financial_dfs['AmineCaptureFacility'].loc['Non-Fuel O&M', :]

		df[2,:] = financial_dfs['CoGenFacility'].loc['Subtotal O&M', :]
		df[3,:] = financial_dfs['CoGenFacility'].loc['Non-Fuel O&M', :]

		df[4,:] = financial_dfs['SteamPlantOnly'].loc['Subtotal O&M', :]
		df[5,:] = financial_dfs['SteamPlantOnly'].loc['Non-Fuel O&M', :]

		df[6,:] = financial_dfs['CoolingTower'].loc['Subtotal O&M', :]
		df[7,:] = financial_dfs['CoolingTower'].loc['Non-Fuel O&M', :]

		df[8,:] = financial_dfs['WaterTreatmentDemineralization'].loc['Subtotal O&M', :]
		df[9,:] = financial_dfs['WaterTreatmentDemineralization'].loc['Non-Fuel O&M', :]

		df[10,:] = financial_dfs['CompressionDehydration'].loc['Subtotal O&M', :]
		df[11,:] = financial_dfs['CompressionDehydration'].loc['Non-Fuel O&M', :]

		df[12,1:] = [df[0,i] + df[2,i]  + df[4,i] + df[6,i] + df[8,i] + df[10,i] for i in range(1, self.MainOptions.total_life)]
		df[13,1:] = [df[1,i] + df[3,i]  + df[5,i] + df[7,i] + df[9,i] + df[11,i] for i in range(1, self.MainOptions.total_life)]


		df[14,:] = financial_dfs['StoragePipeline'].loc['Subtotal O&M', :]
		df[15,:] = financial_dfs['StoragePipeline'].loc['Non-Fuel O&M', :]

		df[16,:] = financial_dfs['EorSalesPipeline'].loc['Subtotal O&M', :]
		df[17,:] = financial_dfs['EorSalesPipeline'].loc['Non-Fuel O&M', :]

		df[18,:] = financial_dfs['CO2PipelineBoostersGaugesMeters'].loc['Subtotal O&M', :]
		df[19,:] = financial_dfs['CO2PipelineBoostersGaugesMeters'].loc['Non-Power O&M', :]


		df[20,:] = financial_dfs['StorageOperationMonitoring'].loc['Storage Site OPEX', :]
		df[21,:] = financial_dfs['StorageOperationMonitoring'].loc['Non-Power O&M', :]

		df[22,:] = project_financial_df['Industrial Insurance'].loc['Annual Premium', :]
		df[23,:] = [project_financial_df['Trust Funds']['PSIC Trust'].loc['Payments to PISC Trust', i] + project_financial_df['Trust Funds']['LTL Trust'].loc['Payments to LTL Trust', i] for i in range(0, self.MainOptions.total_life)]

		df[24,:] = [df[12,i] + df[14,i] + df[16,i] + df[18,i] + df[20,i] + df[22,i] + df[23,i] for i in range(0, self.MainOptions.total_life)]
		df[25,:] = [df[13,i] + df[15,i] + df[17,i] + df[19,i] + df[21,i] + df[22,i] for i in range(0, self.MainOptions.total_life)]

		df[26,1] = df[24,1] / project_financial_df['Total Project CAPEX'].iloc[-1, 0]
		df[26,2: self.MainOptions.in_operation] = np.nan

		df = pd.DataFrame(df, index = ['AmineCaptureFacility', '1 - Non-fuel or power', 'CoGenFacility', '2 - Non-fuel or power', 'SteamPlantOnly', '3 - Non-fuel or power',
										'CoolingTower', '4 - Non-fuel or power', 'WaterTreatmentDemineralization', '5 - Non-fuel or power', 'CompressionDehydration', '6 - Non-fuel or power',
										'Subtotal - Capture Facilities', '1 to 6 - Non-fuel or power', 'StoragePipeline', '7 - Non-fuel or power', 'EorSalesPipeline', '8 - Non-fuel or power',
										'CO2PipelineBoostersGaugesMeters', '9 - Non-fuel or power', 'PreInjectSite', '10 - Non-fuel or power', 'Annual Insurance Premiums', 'Trust Payments',
										'Total Operating Expenses', 'Total Non-fuel or power', 'OPEX % Share CAPEX'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
	
	@st.cache(suppress_st_warning=True)
	def debt_schdule(self, financial_dfs, project_financial_df, CapitalStructure):
		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 4)
		tenor = int(ceil(CapitalStructure.loan_length))

		df[0,1:tenor+1] = 1; df[0,0] = np.nan

		debt = round(project_financial_df['Total Project CAPEX'].iloc[-1, 0] * CapitalStructure.share_debt,1)
		df[-1, 0] = debt

		rate = CapitalStructure.cost_debt
		pmt = np.pmt(rate, tenor, debt, 0)

		df[2,1:] = [pmt * df[0,i] for i in range(1, self.MainOptions.total_life)]

		for i in range(1, self.MainOptions.total_life):
			df[1,i] = df[-1, i-1] * rate * df[0,i]
			df[3,i] = (df[1:3, i].sum() + df[3,i-1]) * df[0,i]

		df = pd.DataFrame(df, index = ['Is Tenor?', 'Interest', 'Payment', 'Loan Balance'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache(suppress_st_warning=True)
	def debt_service(self, financial_dfs, project_financial_df, RevenueReserves, CapitalStructure):
		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 5)
		df_dummy = csf.create_zeros_array(self.MainOptions.total_life, rows = 5)

		OPEX_reserve = (project_financial_df['Operating Costs'].loc['Trust Payments'][1] + project_financial_df['Operating Costs'].loc['Total Operating Expenses'][1]) * RevenueReserves.OM_reserves
		debt_reserve = project_financial_df['Debt Schedule'].loc['Payment'][1] * RevenueReserves.debt_reserves
		df[-1,0] = round(OPEX_reserve + abs(debt_reserve),0)


		OP_income = [project_financial_df['Revenues'].loc['Total Direct Revenues', i] - project_financial_df['Operating Costs'].loc['Total Operating Expenses', i] for i in range(0, self.MainOptions.total_life)]
		df_dummy[0,1:] = [OP_income[i] - project_financial_df['Trust Funds']['PSIC Trust'].loc['Payments to PISC Trust', i] - project_financial_df['Trust Funds']['LTL Trust'].loc['Payments to LTL Trust', i] for i in range(1, self.MainOptions.total_life)]
		df_dummy[1,1:] = [abs(project_financial_df['Debt Schedule'].loc['Payment', i]) for i in range(1, self.MainOptions.total_life)]
		df_dummy[2,1:] = [df_dummy[0,i] - df_dummy[1,i] * CapitalStructure.DSCR for i in range(1, self.MainOptions.total_life)]

		for i in range(1, self.MainOptions.total_life):
			df[0,i] = df[4,i-1]

			if (df_dummy[2,i] > 0) & (df[0,i] < (16*1000000)) & (i < self.MainOptions.in_operation-1):
				df[1,i] = df_dummy[2,i] * 0.05
			else:
				df[1,i] = 0

			if df_dummy[2,i] < 0:
				df_dummy[3,i] = min(-df_dummy[2,i], df[0,i])
			elif i == self.MainOptions.in_operation-1:
				df_dummy[3,i] = df[0,i]
			else:
				df_dummy[3,i] = 0

			df[2,i] = -df_dummy[3,i]

			if df[0:3,i].sum() > 0:
				df[3,i] = (df[0,i] + 0.25 * (df[1,i] + df[2,i])) * 0.03
			else:
				df[3,i] = 0

			df[4,i] = df[0:4, i].sum()

		df_dummy[4,1:] = [(df_dummy[0,i] + df_dummy[3,i]) / df_dummy[1,i] if df_dummy[1,i] > 0 else 0 for i in range(1, self.MainOptions.total_life)]

		df = pd.DataFrame(df, index = ['Beginning Balance', 'Deposits', 'Withdrawls', 'Interest Earnings', 'Ending Balance'])
		df_dummy = pd.DataFrame(df_dummy, index = ['Net Cash Availble for Debt Service', 'Debt Payments', 'DSCR Excess (Shortfall)', '…Transfer from Reserves', 'DSCR'])

		return [df, df_dummy]

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache(suppress_st_warning=True)
	def calc_OPIncome(self, project_financial_df, CapitalStructure):
		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 8)

		tenor = int(ceil(CapitalStructure.loan_length))
		debt = round(project_financial_df['Total Project CAPEX'].iloc[-1, 0] * CapitalStructure.share_debt,1)
		rate = CapitalStructure.cost_debt
		pmt = np.pmt(rate, tenor, debt, 0)

		df[0,:] = [project_financial_df['Revenues'].loc['Total Direct Revenues', i] - project_financial_df['Operating Costs'].loc['Total Operating Expenses', i] for i in range(0, self.MainOptions.total_life)]
		df[1,:] = project_financial_df['Debt Service & Operating Reserve Account'].loc['Interest Earnings']
		df[2,:] = [project_financial_df['Debt Service & Operating Reserve Account'].loc['Beginning Balance', i] if i == self.MainOptions.in_operation-1 else 0 for i in range(0, self.MainOptions.total_life)]
		df[3,:] = [project_financial_df['Trust Funds']['PSIC Trust'].loc['Payments to PISC Trust', i] for i in range(0, self.MainOptions.total_life)]
		df[4,:] = [project_financial_df['Trust Funds']['LTL Trust'].loc['Payments to LTL Trust', i] for i in range(0, self.MainOptions.total_life)]
		df[5,1:tenor+1] = abs(pmt)
		df[6,:] = project_financial_df['Taxes'].loc['Net Taxes Payable']
		df[7,:] = [df[0,i] + df[1,i] + df[2,i] - df[3,i] - df[4,i] - df[5,i] - df[6,i] for i in range(0, self.MainOptions.total_life)]

		df = pd.DataFrame(df, index = ['Gross Profits', 'Interest Income', 'Return of Capital', 'PISC Trust Payments', 'LTL Trust Payments', 'Debt Payments', 'Taxes Payable', 'Net Income'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache(suppress_st_warning=True)
	def calc_taxes(self, financial_dfs, project_financial_df, CapitalStructure):
		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 8)

		MACRS = []
		for i in range(0, self.MainOptions.total_life):
			dummy = []

			for key in financial_dfs.keys():
				if key != 'CO2 Post-Injection Close Monitoring':
					dummy.append(financial_dfs[key].loc['Tax Depreciation', i])
			MACRS.append(sum(dummy))


		OP_income = [project_financial_df['Revenues'].loc['Total Direct Revenues', i] - project_financial_df['Operating Costs'].loc['Total Operating Expenses', i] for i in range(0, self.MainOptions.total_life)]
		
		df[0,:] = project_financial_df['Debt Schedule'].loc['Interest']
		df[1,:] = MACRS
		df[2,:] = [OP_income[i] - df[0:2,i].sum() for i in range(0, self.MainOptions.total_life)]
		df[3,:] = [df[2,i] * CapitalStructure.tax_rate for i in range(0, self.MainOptions.total_life)]

		for i in range(1, self.MainOptions.total_life):
			if df[3,i] < 0:
				df[4,i] = df[3,i] + df[4,i-1]
			else:
				df[4,i] = min(0, df[3,i] + df[4,i-1])

		df[5,:] = [max(df[4,i] + df[3,i], 0) for i in range(0, self.MainOptions.total_life)]
		df[6,:] = [project_financial_df['Revenues'].loc['45Q Storage Credits', i] + project_financial_df['Revenues'].loc['45Q EOR Credits', i] for i in range(0, self.MainOptions.total_life)]
		df[7,1] = sum(project_financial_df['Total ITC'][project_financial_df['Total ITC'].columns[0]])

		df = pd.DataFrame(df, index = ['Interest Expense', 'MACRS Depreciation Expense', 'Taxable Income', 'Gross Taxes Owed (Loss to Carry)',
										'Carried Losses', 'Net Taxes Payable', '45Q/Future Act Tax Credits', 'Investment Tax Credits'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	def equity_sizing(self, project_financial_df, TimeValueMoney):
		df = csf.create_zeros_array(self.MainOptions.total_life, rows = 7)

		df[0,0] = sum(project_financial_df['Total ITC'][project_financial_df['Total ITC'].columns[0]])
		df[1,0] = df[0,0] / TimeValueMoney.tax_ROE[1]

		df[2,:] = project_financial_df['Taxes'].loc['45Q/Future Act Tax Credits']
		df[3,:] = [df[2,i] / TimeValueMoney.tax_ROE[i] for i in range(0, self.MainOptions.total_life)]
		df[4,:] = project_financial_df['Operating Income'].loc['Net Income']
		df[5,:] = [df[4,i] / TimeValueMoney.ROE[i] for i in range(0, self.MainOptions.total_life)]
		df[6,:] = [df[4,i] / TimeValueMoney.NPV[i] for i in range(0, self.MainOptions.total_life)]

		df[3,0] = df[3,1:].sum()
		df[5,0] = df[5,1:].sum()
		df[6,0] = df[6,1:].sum()

		df = pd.DataFrame(df, index = ['Investment Tax Credit', 'PV of ITC Credit', '45Q/Future Act Tax Credits', 'PV of Unused Tax Credits',
										'Net Income - Free Cash Flow to Equity', 'PV @' + str(round(TimeValueMoney.ROE_rate*100,1)) + '% of Excess CFs',
										'PV @' + str(round(TimeValueMoney.NPV_rate*100,1)) + '% of Excess CFs'])
		return df















