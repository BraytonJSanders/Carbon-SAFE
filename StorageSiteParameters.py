import streamlit as st
import pandas as pd
import math
import CarbonSafeFunctions as csf
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class default_values: # Value, Min, Max
	df = pd.DataFrame([[100000.0, 50000.0, 150000.0],
						[10000.0, 5000.0, 15000.0],
						[180000.0, 120000.0, 240000.0],
						[20.0, 5.0, 60.0],
						[25.0, 8.0, 40.0],
						[10.0, 3.0, 20.0],
						[20.0, 5.0, 50.0],
						[5000.0, 2000.0, 10000.0],
						[1.0, 0.1, 5.0],
						[30.0, 10.0, 50.0],
						[2.0, 0.5, 5.0],
						[1.3, 1.0, 3.0]],
						columns = ['Values', 'Min', 'Max'],
						index = ['3D Seismic ($/sqr-mi)', '2D Seismic ($/mile)', 'Permitting Costs ($/sqr-mile)', "Adt'l Costs (%Total, processing etc)", 'Test Well Spacing (sqr-mi/well)',
								'Plug & Abandoment Cost ($/well-ft)', 'P&A Contingency (%Total-P&A)', 'Basic Site Maintenance ($/sqr-mile)',
								'Inject Rate per Well (MtCO2/yr)', 'Backup Well Factor (%Total-Wells)', 'Est. Plume Size per Primary Inj-Well (sqr-mi)', 'MVA Area Cushion Factor (mult)'])
values = default_values()
raw_values = values.df.copy()
indexes = values.df.index
value_column = values.df.columns[0]
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

def set_values(reset_message):
	global values
	global raw_values
	global value_column

	inside = 0

	if st.checkbox('Storage Site Parameters:'):
		inside = 1

		for name in values.df.index:
			values.df.loc[name, value_column] = st.slider(name, values.df.loc[name, 'Min'], values.df.loc[name, 'Max'], values.df.loc[name, value_column], values.df.loc[name, value_column] / 100)
			st.write('')
		if st.button("*Reset to default"):
			values.df = raw_values
			st.success(reset_message)
		csf.main_body_divider()
	return inside
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class StorageSite:
	def __init__(self, reset_message, CaptureFacilities):
		self.inside = set_values(reset_message)
		global values
		global indexes
		global value_column

		self.data = values.df[value_column]
		self.seismic_3D = values.df.loc[indexes[0], value_column]
		self.seismic_2D = values.df.loc[indexes[1], value_column]
		self.permitting = values.df.loc[indexes[2], value_column]
		self.extra_costs = values.df.loc[indexes[3], value_column] / 100
		self.well_spacing = values.df.loc[indexes[4], value_column]
		self.plug_cost = values.df.loc[indexes[5], value_column]
		self.plug_cont = values.df.loc[indexes[6], value_column] / 100
		self.maintenance = values.df.loc[indexes[7], value_column]
		self.inject_rate = values.df.loc[indexes[8], value_column]
		self.backup = values.df.loc[indexes[9], value_column] / 100
		self.plume_size = values.df.loc[indexes[10], value_column]
		self.MVA_cushion = values.df.loc[indexes[11], value_column]

		self.inject_well_count = int(math.ceil(CaptureFacilities.CO2_per_year / self.inject_rate / (1 - self.backup)))
		self.tot_plume_size = self.inject_well_count * self.plume_size
		self.site_area = self.tot_plume_size * 4 # 24
		self.test_well_count = int(math.ceil(self.site_area / self.well_spacing))
		self.MVA_area = self.tot_plume_size * self.MVA_cushion
		self.seal_dual_count = int(math.ceil(self.MVA_area / 4))
		self.vadose_ground_count = 3 * (self.inject_well_count - 1)
		self.test_wells_MVA_periodic = max(1 , math.ceil((self.seal_dual_count - 1) * (self.MVA_area / self.site_area)))




		# st.write(self.site_area)




# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

		