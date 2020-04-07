import streamlit as st
import pandas as pd
import numpy as np

import CarbonSafeFunctions as csf

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class default_values: # Value, Min, Max
	columns = ['Values', 'Min', 'Max', 'Step']
	index_short = ['Well Depth', 'D&C ($/ft)', 'Surface ($/well)']
	index_long = ['Well Depth', 'Well Counts', 'D&C ($/ft)', 'Surface ($/well)']

	well_depth_step = 100
	D_C_step = 10
	surface_step = 1000
	count_step = 1

	strat_wells = pd.DataFrame([[13100, 8000, 20000, well_depth_step],
								[150, 100, 250, D_C_step],
								[1531000, int(1531000 * 0.75), int(1531000 * 1.25), surface_step]],
							columns = columns, index = index_short)

	inject_wells = pd.DataFrame([[12600, 8000, 20000, well_depth_step],
								[156, 100, 250, D_C_step],
								[2350000, int(2350000 * 0.75), int(2350000 * 1.25), surface_step]],
							columns = columns, index = index_short)

	mon_reservoir = pd.DataFrame([[12600, 8000, 20000, well_depth_step],
								[0, 0, 10, count_step],
								[190, 100, 290, D_C_step],
								[25000, int(25000 * 0.75), int(25000 * 1.25), surface_step/2]],
							columns = columns, index = index_long)

	mon_seal = pd.DataFrame([[12100, 8000, 20000, well_depth_step],
								[190, 100, 290, D_C_step],
								[25000, int(25000 * 0.75), int(25000 * 1.25), surface_step/2]],
							columns = columns, index = index_short)

	mon_dual = pd.DataFrame([[12600, 8000, 20000, well_depth_step],
								[210, 100, 300, D_C_step],
								[25000, int(25000 * 0.75), int(25000 * 1.25), surface_step/2]],
							columns = columns, index = index_short)

	mon_groundwater = pd.DataFrame([[500, 100, 1000, well_depth_step/2],
									[250, 150, 350, D_C_step],
									[0, 0, 5000, 50]],
							columns = columns, index = index_short)

	mon_vadose = pd.DataFrame([[10, 1, 100, 1],
									[100, 50, 200, D_C_step],
									[0, 0, 5000, 50]],
							columns = columns, index = index_short)
	water_production = pd.DataFrame([[12800, 8000, 20000, well_depth_step],
								[1, 0, 10, count_step],
								[190, 100, 290, D_C_step],
								[500000, int(500000 * 0.75), int(500000 * 1.25), surface_step]],
							columns = columns, index = index_long)
	water_disposal = pd.DataFrame([[13000, 8000, 20000, well_depth_step],
								[0, 0, 10, count_step],
								[190, 100, 290, D_C_step],
								[200000, int(200000 * 0.75), int(200000 * 1.25), surface_step]],
							columns = columns, index = index_long)

	wells_dic = {'Stratigraphic Test Wells': strat_wells,
				'CO2 Injection Wells': inject_wells,
				'Monitoring Well: In Reservoir': mon_reservoir,
				'Monitoring Well: Above Seal': mon_seal,
				'Monitoring Well: Dual Complete': mon_dual,
				'Monitoring Well: Groundwater': mon_groundwater,
				'Monitoring Well: Vadose Zone': mon_vadose,
				'Water Well: Production': water_production,
				'Water Well: Disposal': water_disposal}


values = default_values()
keys = list(values.wells_dic.keys())
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache()
def create_raw_dictionary(dictionary):
	raw_values = {}
	for well in dictionary.keys():
		raw_values[well] = dictionary[well].copy()
	return raw_values
raw_values = create_raw_dictionary(values.wells_dic)
value_column = values.columns[0]
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

def set_values(reset_message):
	global values
	global raw_values
	global value_column

	inside = 0
	if st.checkbox('Storage Wells Parameters:'):
		inside = 1

		csf.main_body_divider()
		for well in values.wells_dic.keys():
			if st.checkbox('- - ' + well):
				for name in values.wells_dic[well].index:
					mini = int(values.wells_dic[well].loc[name, 'Min'])
					maxi = int(values.wells_dic[well].loc[name, 'Max'])
					current = int(values.wells_dic[well].loc[name, value_column])
					step = int(values.wells_dic[well].loc[name, 'Step'])

					values.wells_dic[well].loc[name, value_column] = st.slider(name, mini, maxi, current, step)

				csf.main_body_divider()
		if st.button("*Reset ALL to default"):
			for well in values.wells_dic.keys():
				values.wells_dic[well] = raw_values[well]
			st.success(reset_message)
		csf.main_body_divider()
	else:
		csf.main_body_divider()
	return inside
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class StorageWells:
	def __init__(self, reset_message, StorageSite):
		global values
		global keys
		global value_column

		self.inside = set_values(reset_message)

		## NOT ENTIRLY DYNAMIC !! 
		well_counts = [StorageSite.test_well_count, StorageSite.inject_well_count, StorageSite.seal_dual_count, StorageSite.seal_dual_count, StorageSite.vadose_ground_count, StorageSite.vadose_ground_count]

		def calculate_well_CAPEX(dictionary):
			counter = 0
			all_CAPEX = []
			abandon_CAPEX = []
			for key in dictionary.keys():
				single_CAPEX = []
				single_abandon_CAPEX = []
				if len(list(dictionary[key].index)) > 3:
					count = int(round(dictionary[key].loc['Well Counts', value_column],0))
				else:
					count = well_counts[counter]
					counter += 1
				single_CAPEX.append(dictionary[key].loc['Well Depth', value_column] * dictionary[key].loc['D&C ($/ft)', value_column] + dictionary[key].loc['Surface ($/well)', value_column])
				single_CAPEX.append(single_CAPEX[0] * count)
				all_CAPEX.append(single_CAPEX[-1])

				single_abandon_CAPEX.append(dictionary[key].loc['Well Depth', value_column] * StorageSite.plug_cost)
				single_abandon_CAPEX.append(single_abandon_CAPEX[0] * count)
				abandon_CAPEX.append(single_abandon_CAPEX[-1])

				df = pd.DataFrame([[single_CAPEX[0], np.nan, np.nan],
									[single_CAPEX[1], np.nan, np.nan]],
									index = ['Est CAPEX ($/well)', 'Well CAPEX ($MM)'],
									columns = ['Values', 'Min', 'Max'])
				dictionary[key] = pd.concat([dictionary[key], df])#, axis = 1)
			return [dictionary, all_CAPEX, abandon_CAPEX]
		calculate_well_CAPEX = calculate_well_CAPEX(values.wells_dic.copy())


		wells_dic = calculate_well_CAPEX[0]

		self.strat_wells = wells_dic[keys[0]][value_column]
		self.inject_wells = wells_dic[keys[1]][value_column]
		self.mon_reservoir = wells_dic[keys[2]][value_column]
		self.mon_seal = wells_dic[keys[3]][value_column]
		self.mon_dual = wells_dic[keys[4]][value_column]
		self.mon_groundwater = wells_dic[keys[5]][value_column]
		self.mon_vadose = wells_dic[keys[6]][value_column]
		self.water_production = wells_dic[keys[7]][value_column]
		self.water_disposal = wells_dic[keys[8]][value_column]
		self.wells_CAPEX = sum(calculate_well_CAPEX[1])
		self.well_count = well_counts[1] + well_counts[2] + well_counts[3]
		self.abandon_CAPEX = (sum(calculate_well_CAPEX[-1]))

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #



