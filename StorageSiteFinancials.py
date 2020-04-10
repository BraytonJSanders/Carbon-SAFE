import streamlit as st
import pandas as pd
import numpy as np

import CarbonSafeFunctions as csf

from SideBar import ModelConstants, SelectBoxOptions

from CaptureFacilitiesFinancials import CaptureFacilitiesFinancial


class StorageSiteFinancial(CaptureFacilitiesFinancial):
	def __init__(self, StorageSite, StorageWells, *args, **kwargs):
		super(StorageSiteFinancial, self).__init__(*args, **kwargs)
		self.StorageSite = StorageSite
		self.StorageWells = StorageWells
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache(suppress_st_warning=True)
	def PreInjectSite(self):
		df = csf.create_zeros_array(self.length, rows = 5)

		seismic_3D = self.StorageSite.seismic_3D * self.StorageSite.site_area
		seismic_2D = self.StorageSite.seismic_2D * (self.StorageSite.site_area ** 0.5)
		permitting = self.StorageSite.permitting * self.StorageSite.site_area
		test_well = self.StorageWells.strat_wells.iloc[-2] * self.StorageSite.test_well_count
		VSP_seismic = (self.StorageWells.inject_wells.iloc[-2] - self.StorageWells.strat_wells.iloc[-2])* self.StorageSite.test_well_count
		total  = sum([seismic_3D, seismic_2D, permitting, test_well, VSP_seismic])

		CAPEX = total / (1 - self.StorageSite.extra_costs)
		ITC = csf.calc_federal_ITC(CAPEX, self.TaxCredits.ITC_CAPEX, self.TaxCredits.invest_tax_cred)

		MACRS = csf.calc_macrs(self.MainOptions.pre_site_macrs, self.length)
		tax_basis_and_straight_line = csf.get_tax_basis_and_straight_line(CAPEX, ITC, self.TaxCredits.income_dep, self.MainOptions.in_operation-1)

		df[0,0] = CAPEX
		df[1,0] = ITC

		df[2,1:] = tax_basis_and_straight_line[0] * MACRS[:-1]
		df[3,:] = tax_basis_and_straight_line[1] * self.in_ops

		# df[2,1:] = [tax_basis_and_straight_line[0] * MACRS[i-1] for i in range(1, self.length)]
		# df[3,1:] = [tax_basis_and_straight_line[1] * self.in_ops[i] for i in range(1, self.length)]

		df[4,:] = csf.book_value_per_year(tax_basis_and_straight_line[0], df[3,:], self.GlobalParameters.min_book_value, self.in_ops) 

		df = pd.DataFrame(df, index = ['CAPEX', 'ITC',
										'Tax Depreciation', 'Straight Line Depreciation', 'Book Value'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache(suppress_st_warning=True)
	def StorageOperationMonitoring(self, CAPEX_pre_inject, CO2SourcePlantResults):
		df = csf.create_zeros_array(self.length, rows = 10)

		CAPEX_wells = (self.StorageWells.wells_CAPEX - self.StorageWells.strat_wells.iloc[-1]) / (1 - self.StorageSite.extra_costs)
		CAPEX = CAPEX_pre_inject + CAPEX_wells
		ITC = csf.calc_federal_ITC(CAPEX, self.TaxCredits.ITC_CAPEX, self.TaxCredits.invest_tax_cred)

		MACRS = csf.calc_macrs(self.MainOptions.well_CAPEX_macrs, self.length)
		tax_basis_and_straight_line = csf.get_tax_basis_and_straight_line(CAPEX, ITC, self.TaxCredits.income_dep, self.MainOptions.in_operation-1)

		total_MVA = ((self.StorageSite.seismic_3D / (1 - self.StorageSite.extra_costs)) * self.StorageSite.MVA_area) + ((self.StorageWells.inject_wells.iloc[-2] - self.StorageWells.strat_wells.iloc[-2]) / (1 - self.StorageSite.extra_costs) * self.StorageSite.test_wells_MVA_periodic)

		df[0,0] = CAPEX_wells
		df[1,0] = ITC

		df[2,:] = (CAPEX_wells * self.TimeValueMoney.escalation_non_rate) * self.TimeValueMoney.escalation * self.in_ops
		df[3,:] = self.StorageWells.well_count * 40000 * self.TimeValueMoney.escalation * self.in_ops
		df[4,:] = total_MVA * self.MonitorSwitchesData.monitor * self.TimeValueMoney.escalation * self.in_ops
		df[5,:] = df[2:5, :].sum(axis = 0) * self.in_ops
		df[6,1:] = [df[5,i] / CO2SourcePlantResults.loc['Cumulative', i] * ModelConstants.out_MM for i in range(1, self.length)] ### NEEDS CORRECTED!
		df[7,1:] = tax_basis_and_straight_line[0] * MACRS[:-1]
		df[8,:] = tax_basis_and_straight_line[1] * self.in_ops

		# df[2,1:] = [(CAPEX_wells * self.TimeValueMoney.escalation_non_rate) * self.TimeValueMoney.escalation[i] * self.in_ops[i] for i in range(1, self.length)]
		# df[3,1:] = [self.StorageWells.well_count * 40000 * self.TimeValueMoney.escalation[i] * self.in_ops[i] for i in range(1, self.length)]
		# df[4,1:] = [total_MVA * self.MonitorSwitchesData.monitor[i] * self.TimeValueMoney.escalation[i] * self.in_ops[i] for i in range(1, self.length)]
		# df[5,1:] = [df[2:5, i].sum() for i in range(1, self.length)]
		# df[6,1:] = [df[5,i] / CO2SourcePlantResults.loc['Cumulative', i] * ModelConstants.out_MM for i in range(1, self.length)] ### NEEDS CORRECTED!
		# df[7,1:] = [tax_basis_and_straight_line[0] * MACRS[i-1] for i in range(1, self.length)]
		# df[8,1:] = [tax_basis_and_straight_line[1] * self.in_ops[i] for i in range(1, self.length)]

		df[9,:] = csf.book_value_per_year(tax_basis_and_straight_line[0], df[8,:], self.GlobalParameters.min_book_value, self.in_ops) 

		df = pd.DataFrame(df, index = ['CAPEX', 'ITC',
									'Non-Power O&M', "Addt' Fixed O&M for Deep Wells", 'Total Periodic MVA', 'Storage Site OPEX', 'OPEX per tCO2',
									'Tax Depreciation', 'Straight Line Depreciation', 'Book Value'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

	@st.cache(suppress_st_warning=True)
	def PostClosure(self):
		df = csf.create_zeros_array(self.length, rows = 5)

		abandon_CAPEX = self.StorageWells.abandon_CAPEX / (1 - self.StorageSite.extra_costs)
		seismic_3D = self.StorageSite.seismic_3D/ (1 - self.StorageSite.extra_costs) * self.StorageSite.site_area
		VSP_survey = 500000 * self.StorageSite.inject_well_count

		df[0, np.where(self.is_closed == 1)[0][0]] = abandon_CAPEX

		df[1,:] = self.StorageSite.maintenance * self.StorageSite.site_area * self.is_closed * self.TimeValueMoney.escalation
		df[2,1:] = [seismic_3D * self.MonitorSwitchesData.survey[i] * self.TimeValueMoney.escalation[i] if i >= sum(self.in_ops) else 0 for i in range(1, self.length)]
		df[3,1:] = [VSP_survey * self.MonitorSwitchesData.survey[i] * self.TimeValueMoney.escalation[i] if i >= sum(self.in_ops) else 0 for i in range(1, self.length)]
		df[4,:] = df[0:4, :].sum(axis = 0)

		# df[1,1:] = [self.StorageSite.maintenance * self.StorageSite.site_area * self.is_closed[i] * self.TimeValueMoney.escalation[i] for i in range(1, self.length)]
		# df[2,1:] = [seismic_3D * self.MonitorSwitchesData.survey[i] * self.TimeValueMoney.escalation[i] if i >= sum(self.in_ops) else 0 for i in range(1, self.length)]
		# df[3,1:] = [VSP_survey * self.MonitorSwitchesData.survey[i] * self.TimeValueMoney.escalation[i] if i >= sum(self.in_ops) else 0 for i in range(1, self.length)]
		# df[4,1:] = [df[0:4, i].sum() for i in range(1, self.length)]

		df = pd.DataFrame(df, index = ['CAPEX', 'Basic O&M', 'Periodic 3D Seismic', 'VSP Well Surveys', 'Total PISC & MVA CAPEX+OPEX'])
		return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #













