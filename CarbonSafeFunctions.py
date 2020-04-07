import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------------------------------------------------------------------------------------------- #

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def import_energy_paths_data(file_name, data_folder_name = 'data/fuel_pricing/'):
	return pd.read_csv(data_folder_name + file_name + '.csv', index_col = 0)
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def import_energy_paths(file_name, data_folder_name = 'data/fuel_pricing/'):
	energy_paths = pd.read_csv(data_folder_name + file_name + '.csv')
	return list(energy_paths[energy_paths.columns[0]])
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def import_plant_data(file_name, data_folder_name = 'data/'):
	return pd.read_csv(data_folder_name + file_name + '.csv', index_col = 0)
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def import_plant_websites(data_folder_name = 'data/'):
	website_data = pd.read_csv(data_folder_name + 'Plant_Websites.csv', index_col = 0)
	return website_data
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache(allow_output_mutation=True, suppress_st_warning=True) # Import raw data for fuel types (Used when data reset is done)
def raw_data(file_name, data_folder_name = 'data/fuel_pricing/', raw_folder_name = 'RAW_data/'):
	return pd.read_csv(data_folder_name + raw_folder_name + file_name + '.csv', index_col=0)
# -------------------------------------------------------------------------------------------------------------------- #
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def import_MACRS_schedule():
	return pd.read_csv('data/MACRS_Schedule.csv', index_col = 0)
MACRS_schedules = import_MACRS_schedule()
# -------------------------------------------------------------------------------------------------------------------- #

def calc_macrs(schedule, length):
	global MACRS_schedules
	MACRS = np.zeros((length))
	MACRS_data = MACRS_schedules.loc[str(schedule)].dropna().copy()
	MACRS[0:len(MACRS_data)] = MACRS_data
	return MACRS
# -------------------------------------------------------------------------------------------------------------------- #

def create_zeros_array(length, rows = 1):
	return np.zeros((rows, length))
# -------------------------------------------------------------------------------------------------------------------- #

def calc_federal_ITC(CAPEX, ITC_share, ITC_rate):
	return (CAPEX * ITC_share * ITC_rate)
# -------------------------------------------------------------------------------------------------------------------- #

def PetraNovaCAPEX_calc(constant, PetraNova, flue_gas, power = 1/4):
	return (constant * PetraNova * (1 / ((flue_gas / 240) ** (power))))

# -------------------------------------------------------------------------------------------------------------------- #

def get_tax_basis_and_straight_line(CAPEX, ITC, ITC_reduction, in_ops):
	tax_basis = (CAPEX-ITC * ITC_reduction)
	return [tax_basis, (tax_basis / in_ops)]
# -------------------------------------------------------------------------------------------------------------------- #

def book_value_per_year(tax_basis, straight_line_yearly, min_book_value, in_ops_yearly):
	df = np.zeros((len(straight_line_yearly)))
	min_value = min_book_value * tax_basis

	for i in range(1, len(straight_line_yearly)):
		if i != 1:
			df[i] = max(df[i-1] - straight_line_yearly[i], min_value) * in_ops_yearly[i]
		else:
			df[i] = tax_basis - straight_line_yearly[i]
	return df
# -------------------------------------------------------------------------------------------------------------------- #

def get_factors(rate, life_span):
	return [((1 + rate) ** x) for x in range(life_span)]
# -------------------------------------------------------------------------------------------------------------------- #

def main_body_divider():
	st.write("_______")

def sidebar_divider():
	st.sidebar.text("- - - - - - - - - - - - - - - - - - -")
# -------------------------------------------------------------------------------------------------------------------- #

def section_header(title, line_above = True):
	if line_above:
		st.write('_________')
	st.header(title); st.subheader('')
# -------------------------------------------------------------------------------------------------------------------- #






