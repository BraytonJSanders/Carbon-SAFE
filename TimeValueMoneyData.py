import streamlit as st
import CarbonSafeFunctions as csf

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class default_values:
	default = [0.0, 3.0, 12.0, 8.0, 10.0, 9.4]
values = default_values()
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

def set_values(reset_message):
	global values

	inside = 0

	if st.checkbox('Infation and Present Value Factors:'):
		inside = 1
		values.default[0] = st.slider("What is the O&M escalation rate per year? (%)", 0.0, 50.0, values.default[0], 0.1)
		st.write('')
		values.default[1] = st.slider("What is the Non-Fuel O&M escalation rate per year? (%)", 0.0, 50.0, values.default[1], 0.1)
		st.write('')
		values.default[2] = st.slider("What is the tax return on equity? (%)", 0.0, 50.0, values.default[2], 0.05)
		st.write('')
		values.default[3] = st.slider("What is the expected Return on Equity? (%)", 0.0, 50.0, values.default[3], 0.05)
		st.write('')
		values.default[4] = st.slider("What is your desired NPV discount rate? (%)", 0.0, 50.0, values.default[4], 0.1)
		st.write('')
		values.default[5] = st.slider("What is your WACC? (%)", 0.0, 50.0, values.default[5], 0.1)
		st.write('')
		
		if st.button("*Restet to default"):
			values.default = [0.0, 3.0, 12.0, 8.0, 10.0, 9.4]
			st.success(reset_message)
		csf.main_body_divider()
	return inside
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

class TimeValueMoney:
	def __init__(self, life_span, reset_message):
		self.inside = set_values(reset_message)
		global values

		self.escalation_rate = values.default[0] / 100
		self.escalation_non_rate = values.default[1] / 100
		self.tax_ROE_rate = values.default[2] / 100
		self.ROE_rate = values.default[3] / 100
		self.NPV_rate = values.default[4] / 100
		self.WACC_rate = values.default[5] / 100

		self.escalation = csf.get_factors(self.escalation_rate, life_span)
		self.escalation_non = csf.get_factors(self.escalation_non_rate, life_span)
		self.tax_ROE = csf.get_factors(self.tax_ROE_rate, life_span)
		self.ROE = csf.get_factors(self.ROE_rate, life_span)
		self.NPV = csf.get_factors(self.NPV_rate, life_span)
		self.WACC = csf.get_factors(self.WACC_rate, life_span)
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
