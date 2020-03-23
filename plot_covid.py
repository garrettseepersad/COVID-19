# %% Load Library Files

# IMPORT PACKAGES
import pandas as pd
import numpy as np
from bokeh.plotting import figure, output_file, show
from bokeh.palettes import all_palettes
from bokeh.palettes import Dark2_5 as palette
from bokeh.models import ColumnDataSource, RangeTool
from bokeh.models import HoverTool
# itertools handles the cycling
import itertools  

from bokeh.layouts import column

# %% Load Classes

def ends(df, x=1):
	""" Return the start and end of the dataframe 
	"""
	return df.head(x).append(df.tail(x))


def count_for_country(covid_data,country):
	""" Calculate sum for each region within a country """
	
	# Create data frame
	d = {'date': [], 'confirmed': [], 'country':[]}
	df = pd.DataFrame(data=d)

	# Extract country of interest
	country_index = covid_data.loc[country]
	unique_dates  = country_index.date.unique()

	# Set date as the "key"
	country_index.set_index('date', inplace = True)
	for unique_date in unique_dates:
		total_per_date = country_index.loc[unique_date]['confirmed'].sum()
		df = df.append({'date': unique_date, 'confirmed': total_per_date, 'country': country},ignore_index=True)

	return df

class COVID:

	def __init__(self):
		
		# Line graph with growing cases
		self.p = figure()
		
		# Range selector
		self.select = figure()

		# Plot from list
		self.plot_countries_by_list = True


	def prepare_COVID_data(self,url,country_listing=None):
		""" Downloads the data 
		1) Read the input URL
		2) Rename the columns
		3) Reshape the data
		Reference : https://www.sharpsightlabs.com/blog/python-data-analysis-covid19-part1/?utm_source=ssl_email_primary&utm_medium=email&utm_campaign=newsletter
		"""
		# READ THE CSV URL
		covid_data_RAW = pd.read_csv(url)

		# RENAME THE COLUMNS
		covid_data = covid_data_RAW.rename(
				columns = { 'Province/State' :'subregion'
							,'Country/Region':'country'
							,'Lat'           :'lat'
							,'Long'          :'long'
							}
				)

		# RESHAPE THE DATA
		# - melt the data into 'tidy' shape
		covid_data = (covid_data.melt(id_vars = ['country','subregion','lat','long']
						,var_name = 'date_RAW'
						,value_name = 'confirmed'
						)
		)

		# CONVERT DATE
		covid_data = covid_data.assign(
				date = pd.to_datetime(covid_data.date_RAW, format='%m/%d/%y')
				)

		# SORT THE DATA
		covid_data = (covid_data
					.filter(['country', 'subregion', 'date', 'lat', 'long', 'confirmed'])
					.sort_values(['country','subregion','lat','long','date'])
					)

		# REMOVE 0's and 1's
		# covid_data = covid_data.replace(0, np.nan)
		# covid_data = covid_data.replace(1, np.nan)
		
		# SORT & REARANGE DATA
		if country_listing is None:
			self.plot_countries_by_list = False

		if self.plot_countries_by_list:
			main_countries = pd.read_csv(country_listing)
			self.countries = main_countries.countries.unique()
		else:
			self.countries = covid_data.country.unique()

		covid_data.set_index('country', inplace = True)
		self.covid_data = covid_data

	def plot_data(self,confirmed_cases_threshold):
		""" Plot the data """

		countries  = self.countries
		covid_data = self.covid_data

		# create a color iterator
		colors = itertools.cycle(palette)

		self.p = figure(title="Confirmed cases",
			plot_width = 1200, 
				plot_height = 400,
				x_axis_type = 'datetime', 
				x_range=(ends(covid_data['date']) )
				)

		for country,color in zip(countries, colors):

			try:
				country_index = covid_data.loc[country]
			except KeyError:
				print("No country " + country)
				continue

			#If confirmed cases are greater than threshold
			if (country_index['confirmed'].max() > confirmed_cases_threshold):

				df = count_for_country(covid_data,country)
				ds = ColumnDataSource(df)

				self.p.line(source = ds, 
					x      = 'date', 
					y      = 'confirmed', 
					line_width = 2, 
					color      = color, 
					legend     = country,
					alpha      = 0.8,
					muted_color= color, 
					muted_alpha=0.2)

				self.p.add_tools(
				HoverTool(
					tooltips=[
						( 'country',   '@country'            ),
						( 'date',   '@date{%F}'              ),
						( 'confirmed',   '@confirmed'        ),
						],
					formatters={
						'@date'        : 'datetime', # use 'datetime' formatter for '@date' field
						},
							
				# mode='hline' # display a tooltip whenever the cursor is vertically in line with a glyph
					)
				)
				self.p.yaxis.axis_label = 'Confirmed cases'
				self.select = figure(title="Drag the middle and edges of the selection box to change the range above",
							plot_height = 130, 
							plot_width  = 1200, 
							y_range     = self.p.y_range,
							x_axis_type = "datetime", 
							y_axis_type = None,
							toolbar_location = None, 
							background_fill_color = "#efefef")

				range_tool = RangeTool(x_range=self.p.x_range)
				range_tool.overlay.fill_color = "navy"
				range_tool.overlay.fill_alpha = 0.2

				self.select.line('date', 'confirmed', source=ds)
				self.select.ygrid.grid_line_color = None
				self.select.add_tools(range_tool)
				self.select.toolbar.active_multi = range_tool

		self.p.legend.location = "top_left" 
		self.p.legend.click_policy="mute"
# %%

url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv'

data  = COVID()
country_listing = "data/main_countries.csv"
data.prepare_COVID_data(url,country_listing)
data.plot_data(0)



# %%
show(column(data.p, data.select))

# %%
