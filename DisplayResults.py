import streamlit as st
import pandas as pd
import numpy as np

import CarbonSafeFunctions as csf
import matplotlib.pyplot as plt



def display_dataframes(financial_dfs, project_financial_df):
	if st.checkbox('View Project DataFrames:'):
		csf.main_body_divider()
		facilities = [key for key in financial_dfs.keys()]
		facilities.insert(0, '-')

		facility_key = st.selectbox('What Facility Financials Would You Like to View?', facilities)
		if facility_key != facilities[0]:
			st.dataframe(financial_dfs[facility_key])
			csf.main_body_divider()

		financials = [key for key in project_financial_df.keys()]
		financials.insert(0, '-')

		financials_key = st.selectbox('What Project Financials Would You Like to View?', financials)
		if financials_key != financials[0]:
			st.dataframe(project_financial_df[financials_key])
		csf.main_body_divider()
	else:
		csf.main_body_divider()
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

def facility_capex(df):
	return df.iloc[0,0] / 1000000
def year_one_OPEX(df, index = 'Subtotal O&M'):
	return df.loc[index, 1] / 1000000
def total_OPEX(df, index = 'Subtotal O&M'):
	return sum(df.loc[index]) / 1000000

@st.cache(suppress_st_warning=True)
def create_cost_summary(financial_dfs, project_financial_df, CaptureFacilities):
	df = csf.create_zeros_array(5, rows = 13)

	df[0,0] = facility_capex(financial_dfs['AmineCaptureFacility']) + facility_capex(financial_dfs['FlueGasTieIn'])
	df[1,0] = facility_capex(financial_dfs['CoGenFacility'])
	df[2,0] = facility_capex(financial_dfs['CoolingTower'])
	df[3,0] = facility_capex(financial_dfs['WaterTreatmentDemineralization'])
	df[4,0] = facility_capex(financial_dfs['CompressionDehydration'])
	df[5,0] = facility_capex(financial_dfs['StoragePipeline'])
	df[6,0] = facility_capex(financial_dfs['EorSalesPipeline'])
	df[7,0] = facility_capex(financial_dfs['CO2PipelineBoostersGaugesMeters'])
	df[8,0] = facility_capex(financial_dfs['PreInjectSite']) + facility_capex(financial_dfs['StorageOperationMonitoring'])
	df[9,0] = (project_financial_df['Total Project CAPEX'].loc["Provision for Owner's Costs"][0] + project_financial_df['Total Project CAPEX'].loc["Debt Reserve & Working Capital"][0]) / 1000000

	df[0,1] = year_one_OPEX(financial_dfs['AmineCaptureFacility']) + year_one_OPEX(financial_dfs['FlueGasTieIn'])
	df[1,1] = year_one_OPEX(financial_dfs['CoGenFacility'])
	df[2,1] = year_one_OPEX(financial_dfs['CoolingTower'])
	df[3,1] = year_one_OPEX(financial_dfs['WaterTreatmentDemineralization'])
	df[4,1] = year_one_OPEX(financial_dfs['CompressionDehydration'])
	df[5,1] = year_one_OPEX(financial_dfs['StoragePipeline'])
	df[6,1] = year_one_OPEX(financial_dfs['EorSalesPipeline'])
	df[7,1] = year_one_OPEX(financial_dfs['CO2PipelineBoostersGaugesMeters'])
	df[8,1] = year_one_OPEX(financial_dfs['StorageOperationMonitoring'], index = 'Storage Site OPEX')
	df[10,1] = (project_financial_df['Trust Funds']['PSIC Trust'].loc['Payments to PISC Trust', 1] + project_financial_df['Trust Funds']['LTL Trust'].loc['Payments to LTL Trust', 1]) / 1000000
	df[11,1] = project_financial_df['Industrial Insurance'].loc['Annual Premium', 1] / 1000000

	df[0,2] = total_OPEX(financial_dfs['AmineCaptureFacility']) + total_OPEX(financial_dfs['FlueGasTieIn'])
	df[1,2] = total_OPEX(financial_dfs['CoGenFacility'])
	df[2,2] = total_OPEX(financial_dfs['CoolingTower'])
	df[3,2] = total_OPEX(financial_dfs['WaterTreatmentDemineralization'])
	df[4,2] = total_OPEX(financial_dfs['CompressionDehydration'])
	df[5,2] = total_OPEX(financial_dfs['StoragePipeline'])
	df[6,2] = total_OPEX(financial_dfs['EorSalesPipeline'])
	df[7,2] = total_OPEX(financial_dfs['CO2PipelineBoostersGaugesMeters'])
	df[8,2] = total_OPEX(financial_dfs['StorageOperationMonitoring'], index = 'Storage Site OPEX')
	df[10,2] = (sum(project_financial_df['Trust Funds']['PSIC Trust'].loc['Payments to PISC Trust']) + sum(project_financial_df['Trust Funds']['LTL Trust'].loc['Payments to LTL Trust'])) / 1000000
	df[11,2] = sum(project_financial_df['Industrial Insurance'].loc['Annual Premium']) / 1000000


	df[:,-2] = [df[i, 0:4].sum() for i in range(df.shape[0])]
	df[:,-1] = [df[i,-2] / CaptureFacilities.project for i in range(df.shape[0])]

	df[-1,:] = [df[:-1,i].sum() for i in range(df.shape[1])]

	df = pd.DataFrame(df, index = ['Amine Capture & Tie-In', 'CoGen Steam+Power Plant', 'Cooling Tower', 'Water Treatment', 'Compression', 'Storage Site Pipeline', 'EOR Sales Pipeline',
									'Pipeline Meters/Boosters', 'Storage Site', "Owner's Costs, Reserve & WC", 'Total Trust Payments', 'Industrial Insurance', 'TOTAL'],
						columns = ['CAPEX', 'Year-One OPEX', 'Total OPEX', 'ALL-IN', 'per TON'])

	return df
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

def horizontal_bar_chart(df, selection):
	x = df[selection][:-1]
	plt.rcParams.update({'font.size': 7})
	plt.gcf().subplots_adjust(left=0.25)
	plt.barh(x.index, x)
	if selection == 'per TON':
		label = 'USD$ per Ton C02 - [ALL-IN]'
	else:
		label = 'Millions (USD$)'

	plt.xlabel(label)
	plt.title(selection)

	plt.grid(which = 'both', axis = 'x')
	st.pyplot()

def pie_chart(dff, selection):
	df = dff.copy()
	df = df[selection][:-1]
	sum_values = sum(df)

	if selection == 'per TON':
		drop = 1.5
		label = '$' + str(drop) + ' per Ton C02'
		label_2 = ' per Ton C02'
	elif selection == 'Year-One OPEX':
		drop = 1
		label = '$' + str(drop) + ' Million'
		label_2 = ' Million'
		
	else:
		drop = 3
		label = '$' + str(drop) + ' Million'
		label_2 = ' Million'

	df = df[df >= drop]
	data = df.copy()
	recipe = df.index.copy()

	fig, ax = plt.subplots(figsize=(6.5, 3), subplot_kw=dict(aspect="equal"))
	wedges, texts = ax.pie(data, wedgeprops=dict(width=0.5), startangle=-40)
	bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
	kw = dict(arrowprops=dict(arrowstyle="-"),
	          bbox=bbox_props, zorder=0, va="center")
	for i, p in enumerate(wedges):
	    ang = (p.theta2 - p.theta1)/2. + p.theta1
	    y = np.sin(np.deg2rad(ang))
	    x = np.cos(np.deg2rad(ang))
	    horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
	    connectionstyle = "angle,angleA=0,angleB={}".format(ang)
	    kw["arrowprops"].update({"connectionstyle": connectionstyle})
	    ax.annotate(recipe[i] + ': ' +str(round(data[i]/sum_values*100,1)) + '%', xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
	                horizontalalignment=horizontalalignment, **kw)
	ax.set_title(selection + ' Percentages')

	st.text(selection + ': $' +str(round(dff[selection][-1],2)) + label_2)
	st.pyplot()
	st.text('*Note: Values less that ' + label + ' (' + str(round(drop / sum_values * 100,1)) + '% of total) are dropped for clarity.')

def individual_cost_summary(df):
	options = list(df.columns)
	options.insert(0, '-')
	selection = st.selectbox('Isolate One Display:', options)

	if selection != options[0]:
		horizontal_bar_chart(df, selection)
		pie_chart(df, selection)
	csf.main_body_divider()
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

@st.cache
def create_summary_df_for_graph(MainOptions, financial_dfs, project_financial_df):
	in_ops = MainOptions.in_operation
	df =  csf.create_zeros_array(in_ops, rows = 8)

	df[0,:] = project_financial_df['Operating Income'].loc['Net Income'][:in_ops] / 1000000
	df[1,1] = sum(project_financial_df['Total ITC'][project_financial_df['Total ITC'].columns[0]]) / 1000000
	df[2,:] = [(project_financial_df['Revenues'].loc['45Q Storage Credits', i] + project_financial_df['Revenues'].loc['45Q EOR Credits', i]) / 1000000 for i in range(0, in_ops)]
	df[3,:] = project_financial_df['Revenues'].loc['CO2 Sold to EOR'][:in_ops] / 1000000
	df[4,:] = project_financial_df['Revenues'].loc['Excess CoGen Power Sold'][:in_ops] / 1000000
	df[5,:] = [(project_financial_df['Revenues'].loc['Green "EOR" Electron Sales (to CA)', i] + project_financial_df['Revenues'].loc['Green "Storage" Electron Sales (to CA)', i]) / 1000000 for i in range(0, in_ops)]
	df[6,:] = [(project_financial_df['Revenues'].loc['"EOR" Tradable Offsets', i] + project_financial_df['Revenues'].loc['"Storage" Tradable Offsets', i]) / 1000000 for i in range(0, in_ops)]
	df[7,:] = [(project_financial_df['Operating Costs'].loc['Total Operating Expenses', i] + project_financial_df['Operating Income'].loc['PISC Trust Payments', i] + project_financial_df['Operating Income'].loc['LTL Trust Payments', i] + project_financial_df['Operating Income'].loc['Debt Payments', i] + project_financial_df['Operating Income'].loc['Taxes Payable', i]) / 1000000 for i in range(0, in_ops)]


	df = pd.DataFrame(df, index = ['Net Income', 'ITC Tax Credit', '45Q Tax Credits', 'CO2 Sold to EOR', 'Excess CoGen Sales', 'Green Electron Sales', 'Tradable Offset Sales', 'Operating Costs'])
	return df



def multiple_display_graph(merged_df):
	st.subheader('Summary Graph:')
	merged_df = merged_df[merged_df.columns[1:]]
	merged_df = merged_df.transpose()

	ax = merged_df[['45Q Tax Credits', 'CO2 Sold to EOR', 'Excess CoGen Sales', 'Green Electron Sales', 'Tradable Offset Sales', 'Operating Costs']].plot(secondary_y=False)
	merged_df[['Net Income', 'ITC Tax Credit']].plot(kind='bar', ax=ax, width = 0.8)
	plt.yticks(np.arange(min(merged_df.min()), max(merged_df.max())+10, 10))
	plt.grid(which = 'both', axis = 'y')
	plt.xlabel('Operating Year')
	plt.ylabel('Millions USD$')
	plt.title('Revenues, OPEX and Tax Credits')
	x = plt.gca()
	st.pyplot()
	csf.main_body_divider()












