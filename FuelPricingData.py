import matplotlib.pyplot as plt
import pandas_datareader as pdr
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import quandl

from SideBar import SelectBoxOptions
import CarbonSafeFunctions as csf

quandl.ApiConfig.api_key = 'siptc6ujzdFqDFG1AKWw'
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

def set_values(reset_message):
	engery_df = csf.import_energy_paths_data('Energy_Price_Paths_Data')
	raw_engery_df = csf.raw_data('Energy_Price_Paths_Data')
	inside = 0

	if st.checkbox('Change Fuel Pricing Assumptions:'):
		inside = 1
		st.text('See full dataframe below...')
		selection = st.selectbox('Select a Fuel to Edit:', engery_df.index)

		for name in engery_df.columns[2:]:
			current =  float(engery_df.loc[selection][name])
			minimum = current * 0.5 if current > 0 else 0.0
			maximum = current * 1.5 if current > 0 else 5.0
			engery_df.loc[selection, name] = st.slider(name, minimum, maximum, current, current/100)

		if st.button('*Reset ' + selection + ' assumption to default values.'):
			engery_df.loc[selection, engery_df.columns[2:]] = raw_engery_df.loc[selection, engery_df.columns[2:]].copy()
			st.success(reset_message)
		st.dataframe(engery_df)
		csf.main_body_divider()

	if st.checkbox('Change Fuel Pricing Paths:'):
		inside = 1
		for fuel in engery_df.index:
			engery_df.loc[fuel, 'Price Path'] = st.selectbox(fuel, SelectBoxOptions.energy_paths[engery_df.loc[fuel, 'Price Path']])
		csf.main_body_divider()
	return [engery_df, inside]
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class FuelData:
	def __init__(self, reset_message):
		engery_df = set_values(reset_message)
		self.inside = engery_df[1]
		engery_df = engery_df[0]

		self.dataframe = engery_df
		self.WTI = engery_df.loc['WTI Crude']
		self.HH_NG = engery_df.loc['Henry Hub Natural Gas']
		self.Com_NG = engery_df.loc['Commercial Natural Gas']
		self.Ind_NG = engery_df.loc['Industrial Natural Gas']
		self.Ind_Elec = engery_df.loc['Industrial Electricity']
		self.Whol_Elec = engery_df.loc['Wholesale Electricity']
		self.Coal = engery_df.loc['Powder River Coal']
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

def constant_path(FuelData, fuel):
	constant_price = FuelData.loc[fuel, 'Start/Constant']
	return constant_price
# -------------------------------------------------------------------------------------------------------------------- #

def linear_growth(FuelData, fuel, total_life, fuel_pricing_array):
	constant = (FuelData.loc[fuel, 'Trend Target'] - FuelData.loc[fuel, 'Start/Constant'])/(FuelData.loc[fuel, 'Trend Periods']-1)
	maximum = FuelData.loc[fuel, 'Maximum']
	minimum = FuelData.loc[fuel, 'Minimum']

	for i in range(1, total_life):
		previous = fuel_pricing_array[i-1]
		if (previous + constant) >= maximum:
			fuel_pricing_array[i] = maximum
		elif (previous + constant) <= minimum:
			fuel_pricing_array[i] = minimum
		else:
			fuel_pricing_array[i] = previous + constant
	return fuel_pricing_array
# -------------------------------------------------------------------------------------------------------------------- #

def exponential_growth(FuelData, fuel, total_life, fuel_pricing_array):
	escalation = FuelData.loc[fuel, 'Escalation (%/yr)'] / 100
	maximum = FuelData.loc[fuel, 'Maximum']
	minimum = FuelData.loc[fuel, 'Minimum']

	for i in range(1, total_life):
		previous = fuel_pricing_array[i-1]
		st.text(previous)
		if (previous * (1 + escalation)) >= maximum: # Maximum
			fuel_pricing_array[i] = maximum
		elif (previous * (1 + escalation)) <= minimum: # Minimum
			fuel_pricing_array[i] = minimum
		else:
			fuel_pricing_array[i] = (previous * (1 + escalation))
	return fuel_pricing_array
# -------------------------------------------------------------------------------------------------------------------- #

def stochastic_growth(FuelData, fuel, total_life, fuel_pricing_array):
	distribution = np.random.normal((FuelData.loc[fuel, 'Mean'] / 100), (FuelData.loc[fuel, 'StdDev'] / 100), (total_life,))
	maximum = FuelData.loc[fuel, 'Maximum']
	minimum = FuelData.loc[fuel, 'Minimum']

	for i in range(1, total_life):
		previous = fuel_pricing_array[i-1]
		if (previous * (1 + distribution[i])) >= maximum:
			fuel_pricing_array[i] = maximum
		elif (previous * (1 + distribution[i])) <= minimum:
			fuel_pricing_array[i] = minimum
		else:
			fuel_pricing_array[i] = (previous * (1 + distribution[i]))
	return fuel_pricing_array
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def import_current_WTI_data(fuel):
	fuel_data_keys = {'WTI Crude': ['CL=F', 'PET_RWTC_A'],
						'Henry Hub Natural Gas': ['NG=F', 'NG_RNGWHHD_A']}
	year = datetime.today()
	YTD_data = pdr.DataReader(fuel_data_keys[fuel][0], start = '1/1/' + str(year.year), data_source = 'yahoo')
	historical_data = quandl.get('EIA/' + fuel_data_keys[fuel][1])
	current = YTD_data.iloc[-1]['Close']
	new_entry = pd.DataFrame([round(YTD_data['Close'].mean(),2)], index = [year.strftime('%Y-%M-%d')], columns = ['Value'])
	return [pd.concat([historical_data, new_entry], axis = 0), current]
# -------------------------------------------------------------------------------------------------------------------- #

def stochastic_live(total_life, fuel):
    imported = import_current_WTI_data(fuel)
    data = imported[0]
    
    data['% Change'] = data.pct_change()
    data_stats_20 = data.iloc[-20:]['Value'].describe()
    data_stats = data['% Change'].describe()

    minimum = min(data_stats_20.loc['min'], imported[1] * (1 + (5 / 100)))
    maximum = max(data_stats_20.loc['max'], imported[1] * (1 + (5 / 100)))
    mean = data_stats.loc['mean']
    std = data_stats.loc['std']
    
    distribution = np.random.normal(mean, std, total_life)

    fuel_pricing_array = np.zeros((total_life))
    fuel_pricing_array[0] = imported[1]
    
    for i in range(1, total_life):
        previous = fuel_pricing_array[i-1]
    
        if (previous * (1 + distribution[i])) >= maximum:
            fuel_pricing_array[i] = maximum
        elif (previous * (1 + distribution[i])) <= minimum:
            fuel_pricing_array[i] = minimum
        else:
            fuel_pricing_array[i] = (previous * (1 + distribution[i]))
    return fuel_pricing_array
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def calc_fuel_prices(FuelData, MainOptions):
	fuel_pricing_array = np.zeros((len(FuelData.dataframe.index), MainOptions.total_life))
	fuel_pricing_array[:, 0] = np.array(FuelData.dataframe['Start/Constant'])

	for (i, fuel) in enumerate(FuelData.dataframe.index):
		if FuelData.dataframe.loc[fuel, 'Price Path'] == SelectBoxOptions.energy_path[1]: # Linear Growth
			fuel_pricing_array[i, :] = linear_growth(FuelData.dataframe, fuel, MainOptions.total_life, fuel_pricing_array[i, :])

		elif FuelData.dataframe.loc[fuel, 'Price Path'] == SelectBoxOptions.energy_path[2]: # Exponential Growth
			fuel_pricing_array[i, :] = exponential_growth(FuelData.dataframe, fuel, MainOptions.total_life, fuel_pricing_array[i, :])

		elif FuelData.dataframe.loc[fuel, 'Price Path'] == SelectBoxOptions.energy_path[3]: # Stochastic Growth
			fuel_pricing_array[i, :] = stochastic_growth(FuelData.dataframe, fuel, MainOptions.total_life, fuel_pricing_array[i, :])

		elif FuelData.dataframe.loc[fuel, 'Price Path'] == SelectBoxOptions.energy_path[4]: # Stochastic Growth LIVE
			if (fuel == 'WTI Crude') | (fuel == 'Henry Hub Natural Gas'): # Stochastic LIVE only works for WTI or HH NG, else do normal Stochastic
				fuel_pricing_array[i, :] = stochastic_live(MainOptions.total_life, fuel)
			else:
				fuel_pricing_array[i, :] = stochastic_growth(FuelData.dataframe, fuel, MainOptions.total_life, fuel_pricing_array[i, :])

		else: # Constant
			fuel_pricing_array[i, :] = constant_path(FuelData.dataframe, fuel)
	return fuel_pricing_array

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class FuelPrices:
	def __init__(self, FuelData, MainOptions):
		fuel_pricing_array = calc_fuel_prices(FuelData, MainOptions)

		self.WTI_path = fuel_pricing_array[0, :]
		self.HH_NG_path = fuel_pricing_array[1, :]
		self.Com_NG_path = fuel_pricing_array[2, :]
		self.Ind_NG_path = fuel_pricing_array[3, :]
		self.Ind_Elec_path = fuel_pricing_array[4, :]
		self.Whol_Elec_path = fuel_pricing_array[5, :]
		self.Coal_path = fuel_pricing_array[6, :]
		self.fuel_pricing_df = pd.DataFrame(fuel_pricing_array, index = FuelData.dataframe.index)

		self.elec_purchase = self.fuel_pricing_df.loc['Industrial Electricity'] if MainOptions.elec_purchase == SelectBoxOptions.Elec_Power_Rates[0] else self.fuel_pricing_df.loc['Wholesale Electricity']
		self.elec_sold = self.fuel_pricing_df.loc['Industrial Electricity'] if MainOptions.elec_sold == SelectBoxOptions.Elec_Power_Rates[0] else self.fuel_pricing_df.loc['Wholesale Electricity']
		
		if MainOptions.gas_purchase == SelectBoxOptions.NG_Power_Rates[0]: # ['Henry Hub', 'Commercial', 'Industrial']
			self.ng_purchase = self.fuel_pricing_df.loc['Henry Hub Natural Gas']
		elif MainOptions.gas_purchase == SelectBoxOptions.NG_Power_Rates[1]:
			self.ng_purchase = self.fuel_pricing_df.loc['Commercial Natural Gas']
		else:
			self.ng_purchase = self.fuel_pricing_df.loc['Industrial Natural Gas']
		# st.dataframe(self.ng_purchase)

	def graph_fuel_paths(self, FuelData, in_operation = 25):
		if st.checkbox('View Fuel Pricing Over Time:'):
			selection = st.multiselect('What path would you like to view?', FuelData.dataframe.index)
			if len(selection) > 0:
				data = self.fuel_pricing_df.loc[selection].transpose()
				data = data.iloc[:in_operation]
				data.plot()
				plt.grid(which = 'both', axis = 'y')
				plt.xlabel('Operating Year')
				plt.ylabel('USD$ per Unit')
				plt.title('Fuel Pricing Over Time')
				x = plt.gca()
				st.pyplot()
				st.dataframe(data.transpose())
			csf.main_body_divider()

	@st.cache(suppress_st_warning=True)
	def cal_CO2_price_and_green(self, RevenueReserves, MainOptions, TimeValueMoney):
		df = csf.create_zeros_array(MainOptions.total_life, rows = 3)

		if MainOptions.CO2_path == SelectBoxOptions.CO2_to_EOR_Price_Path[-1]: # CO2_to_EOR_Price_Path = ['Tried to WTI Crude', 'Fixed Price']
			df[0,:] = RevenueReserves.CO2_fixed
		else:
			mini = 0
			maxi = 20
			r = TimeValueMoney.escalation_rate
			transport = RevenueReserves.CO2_transport
			tied = RevenueReserves.CO2_WTI
			df[0,1:] = [min(max(transport * ((1 + r) ** (i-1)) + (tied * self.WTI_path[i]), mini), maxi) for i in range(1, MainOptions.total_life)]

		df[1,1:] = [self.elec_sold[i] * (1 + RevenueReserves.green_premium / 2) - self.elec_sold[i] for i in range(1, MainOptions.total_life)]
		df[2,1:] = [self.elec_sold[i] * (1 + RevenueReserves.green_premium) - self.elec_sold[i] for i in range(1, MainOptions.total_life)]

		df = pd.DataFrame(df, index = ['CO2-EOR Price ($/Mcf)', 'EOR Carbon "Green" Premium ($/MWh)', 'Sequestration "Green" Premium ($/MWh)'])
		return df



# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

