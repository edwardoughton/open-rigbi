## Visualization script for climate scenarios
library(tidyverse)
library(ggpubr)

###################
##### Coastal flooding
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder,'..','data','processed','results','validation')
setwd(data_directory)

data = read_csv('scenario_stats.csv')

data$flooded_area_km2 = gsub("-", 'NA', data$flooded_area_km2)
data$flooded_area_km2 = as.numeric(as.character(data$flooded_area_km2))
data$flooded_area_km2 = round(data$flooded_area_km2 / 1e6,3)

data = data[data$hazard == 'inuncoast',]

country_info = read_csv(file.path(folder, '..', 'data','countries.csv'))
country_info = select(country_info, iso3, continent, flood_region)
data = merge(data, country_info,by="iso3")

data = data[
  data$climate_scenario == 'historical' | 
    data$climate_scenario == 'rcp4p5' | 
    data$climate_scenario == "rcp8p5",]

data$climate_scenario = factor(data$climate_scenario,
                               levels=c("historical","rcp4p5","rcp8p5"),
                               labels=c("Historical","RCP4.5","RCP8.5")
)

data$return_period = factor(data$return_period,
                            levels=c(
                              "rp0100",
                              "rp0250",
                              "rp0500",
                              "rp1000"
                            ),
                            labels=c(
                              "1-in-100-Years",
                              "1-in-250-Years",
                              "1-in-500-Years",
                              "1-in-1000-Years"
                            )
)

#convert to probability_of_exceedance 
data$probability = ''
data$probability[data$return_period == "1-in-100-Years"] = "1%" # (1/100) * 100 = 1%
data$probability[data$return_period == "1-in-250-Years"] = "0.4%" # (1/250) * 100 = .4%
data$probability[data$return_period == "1-in-500-Years"] = "0.2%" # (1/500) * 100 = .2%
data$probability[data$return_period == "1-in-1000-Years"] = "0.1%" # (1/1000) * 100 = .1%


data$probability = factor(data$probability,
                          levels=c(
                            "0.1%",
                            "0.2%",
                            "0.4%",
                            "1%"
                          )
)

data$interaction = paste(data$climate_scenario, data$year)

data$interaction = factor(data$interaction,
                          levels=c(
                            "Historical hist", 
                            "Historical 2030",
                            "Historical 2050",
                            "Historical 2080",
                            "RCP4.5 2030",
                            "RCP8.5 2030",
                            "RCP4.5 2050",
                            "RCP8.5 2050",
                            "RCP4.5 2080",
                            "RCP8.5 2080"),
                          labels = c(
                            "Historical\n1980", 
                            "Historical\n2030",
                            "Historical\n2050",
                            "Historical\n2080",
                            "RCP4.5\n2030",
                            "RCP8.5\n2030",
                            "RCP4.5\n2050",
                            "RCP8.5\n2050",
                            "RCP4.5\n2080",
                            "RCP8.5\n2080"),
)

data$continent = factor(data$continent,
                        levels=c(
                          "Africa",
                          "Asia",
                          "Europe",
                          "North America",
                          "Oceania",
                          "South America"
                        ),
                        labels=c(
                          "Africa",
                          "Asia",
                          "Europe",
                          "North\nAmerica",
                          "Oceania",
                          "South\nAmerica"
                        )
)

data$flood_region = factor(data$flood_region,
                           levels=c(
                             "Brazil",
                             "Central America & Caribbean",
                             "China",
                             "Japan & Korea",
                             "Middle East & North Africa",
                             "North America",
                             "Oceania",
                             "Rest of FSU",
                             "Russia",
                             "South America",
                             "South Asia",
                             "Southeast Asia",
                             "Sub-Saharan Africa",
                             "Western Europe"
                           ),
                           labels=c(
                             "Brazil",
                             "CAC", #Central America\n& Caribbean
                             "China",
                             "Japan & Korea",
                             "MENA", #"Middle East\n& North Africa",
                             "N. America", #"North\nAmerica",
                             "Oceania",
                             "Rest of FSU",
                             "Russia",
                             "S. America", #"South\nAmerica",
                             "S. Asia", #"South\nAsia",
                             "SE. Asia", #"Southeast\nAsia",
                             "SSA", #"Sub-Saharan\nAfrica",
                             "W. Europe" #"Western\nEurope"
                           )
)

# write_csv(data, file.path(folder,'country_scenario_stats.csv'))

data_continent = data %>%
  group_by(interaction, continent, probability, climate_scenario) %>%
  summarize(
    # mean_depth = mean(mean_depth, na.rm = TRUE),
    flooded_area_km2 = sum(flooded_area_km2, na.rm = TRUE)
  )

# write_csv(data_continent, file.path(folder,'global_scenario_stats.csv'))

df_errorbar <-
  data_continent |>
  group_by(continent, interaction, probability) |>
  summarize(
    # low = sum(low),
    flooded_area_km2 = sum(flooded_area_km2),
    # high = sum(high)
  ) |>
  group_by(interaction, probability) |>
  summarize(
    continent = 'Africa',
    # low = sum(low),
    flooded_area_km2 = sum(flooded_area_km2),
    # high = sum(high)
  )
max_y_value = max(data_continent$flooded_area_km2, na.rm=TRUE)

plot1 = 
  ggplot(data_continent, 
         aes(x=continent, y=flooded_area_km2, fill=interaction)) + #, income_group
  geom_bar(stat="identity", position = position_dodge()) +
  # geom_text(data = df_errorbar, aes(label = paste(round(flooded_area_km2,2),"m")),
  #           size = 1.5,
  #           position = position_dodge(1),
  #           vjust =-.5, hjust =.5, angle = 90) +
  theme(legend.position = '',
        axis.text.x = element_text(angle=90, hjust=1, vjust=.5, size=7)) +
  labs(colour=NULL,
       # title = "Global Sum of Flooded Coastal Area by Scenario",
       # subtitle = "Reported by Continent, Annual Probability, Year and Climate Scenario.", 
       x = "", y = "Flooded Area\n(Millions km^2)", fill=NULL) +
  theme(legend.position = 'bottom', panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=7, title='Scenario')
  ) +
  scale_fill_viridis_d(direction=-1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+.02)) +
  facet_wrap(~probability, ncol=4, nrow=1)


data_region = data %>%
  group_by(interaction, flood_region, probability, climate_scenario) %>%
  summarize(
    # mean_depth = mean(mean_depth, na.rm = TRUE),
    flooded_area_km2 = sum(flooded_area_km2, na.rm = TRUE)
  )

# write_csv(data_continent, file.path(folder,'global_scenario_stats.csv'))

df_errorbar <-
  data_region |>
  group_by(flood_region, interaction, probability) |>
  summarize(
    # low = sum(low),
    flooded_area_km2 = sum(flooded_area_km2),
    # high = sum(high)
  ) #|>
  # group_by(interaction, probability) |>
  # summarize(
  #   flood_region = 'Brazil',
  #   # low = sum(low),
  #   flooded_area_km2 = sum(flooded_area_km2),
  #   # high = sum(high)
  # )
max_y_value = max(data_region$flooded_area_km2, na.rm=TRUE)

plot2 = 
  ggplot(data_region, 
         aes(x=flood_region, y=flooded_area_km2, fill=interaction)) + #, income_group
  # geom_bar(stat="identity", position='stack') +
  geom_bar(stat="identity", position = position_dodge()) +
  # geom_text(data = df_errorbar, aes(label = paste(round(flooded_area_km2,2),"m")),
  #           size = 1.5,
  #           # position = position_dodge(1),
  #           vjust =-.5, hjust =.5, angle = 0) +
  theme(legend.position = '',
        axis.text.x = element_text(angle=90, hjust=1, vjust=.5, size=7)) +
  labs(colour=NULL,
       # title = "Global Sum of Flooded Coastal Area by Scenario",
       # subtitle = "Reported by Flood Region, Annual Probability, Year and Climate Scenario.", 
       x = "", y = "Flooded Area\n(Millions km^2)", fill=NULL) +
  theme(legend.position = 'bottom', panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=7, title='Flood\nRegion')
  ) +
  scale_fill_viridis_d(direction=-1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+.01)) +
  facet_wrap(~probability, ncol=4, nrow=1)

###################
##### Riverine flooding
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder,'..','data','processed','results','validation')
setwd(data_directory)

data = read_csv('scenario_stats.csv')

data$flooded_area_km2 = gsub("-", 'NA', data$flooded_area_km2)
data$flooded_area_km2 = as.numeric(as.character(data$flooded_area_km2))
data$flooded_area_km2 = round(data$flooded_area_km2 / 1e6,5)

country_info = read_csv(file.path(folder, '..', 'data','countries.csv'))
country_info = select(country_info, iso3, continent, flood_region)
data = merge(data, country_info,by="iso3")

data = data[data$hazard == 'inunriver',]
# data = data[data$iso3 == 'USA',]

data = data[
  data$climate_scenario == 'historical' | 
    data$climate_scenario == 'rcp4p5' | 
    data$climate_scenario == "rcp8p5",]

data$climate_scenario = factor(data$climate_scenario,
                               levels=c("historical","rcp4p5","rcp8p5"),
                               labels=c("Historical","RCP4.5","RCP8.5")
)


# test = data %>%
#   group_by(climate_scenario, year, return_period) %>%
#   summarize(
#     mean_depth = mean(mean_depth, na.rm = TRUE),
#     flooded_area_km2 = mean(flooded_area_km2, na.rm = TRUE),
#   )
# write_csv(test, file.path(folder, 'test.csv'))

data$return_period = factor(data$return_period,
                            levels=c(
                              "rp00100",
                              "rp00250",
                              "rp00500",
                              "rp01000"
                            ),
                            labels=c(
                              "1-in-100-Years",
                              "1-in-250-Years",
                              "1-in-500-Years",
                              "1-in-1000-Years"
                            )
)

#convert to probability_of_exceedance 
data$probability = ''
data$probability[data$return_period == "1-in-100-Years"] = "1%" # (1/100) * 100 = 1%
data$probability[data$return_period == "1-in-250-Years"] = "0.4%" # (1/250) * 100 = .4%
data$probability[data$return_period == "1-in-500-Years"] = "0.2%" # (1/500) * 100 = .2%
data$probability[data$return_period == "1-in-1000-Years"] = "0.1%" # (1/1000) * 100 = .1%

data$probability = factor(data$probability,
                          levels=c(
                            "0.1%",
                            "0.2%",
                            "0.4%",
                            "1%"
                          )
)

data$interaction = paste(data$climate_scenario, data$year)

data$interaction = factor(data$interaction,
                          levels=c(
                            "Historical 1980",
                            "RCP4.5 2030",
                            "RCP8.5 2030",
                            "RCP4.5 2050",
                            "RCP8.5 2050",
                            "RCP4.5 2080",
                            "RCP8.5 2080"),
                          labels=c(
                            "Historical\n1980",
                            "RCP4.5\n2030",
                            "RCP8.5\n2030",
                            "RCP4.5\n2050",
                            "RCP8.5\n2050",
                            "RCP4.5\n2080",
                            "RCP8.5\n2080"),
)

data$continent = factor(data$continent,
                        levels=c(
                          "Africa",
                          "Asia",
                          "Europe",
                          "North America",
                          "Oceania",
                          "South America"
                        ),
                        labels=c(
                          "Africa",
                          "Asia",
                          "Europe",
                          "North\nAmerica",
                          "Oceania",
                          "South\nAmerica"
                        )
)

data$flood_region = factor(data$flood_region,
                           levels=c(
                             "Brazil",
                             "Central America & Caribbean",
                             "China",
                             "Japan & Korea",
                             "Middle East & North Africa",
                             "North America",
                             "Oceania",
                             "Rest of FSU",
                             "Russia",
                             "South America",
                             "South Asia",
                             "Southeast Asia",
                             "Sub-Saharan Africa",
                             "Western Europe"
                           ),
                           labels=c(
                             "Brazil",
                             "CAC", #Central America\n& Caribbean
                             "China",
                             "Japan & Korea",
                             "MENA", #"Middle East\n& North Africa",
                             "N. America", #"North\nAmerica",
                             "Oceania",
                             "Rest of FSU",
                             "Russia",
                             "S. America", #"South\nAmerica",
                             "S. Asia", #"South\nAsia",
                             "SE. Asia", #"Southeast\nAsia",
                             "SSA", #"Sub-Saharan\nAfrica",
                             "W. Europe" #"Western\nEurope"
                           )
)
#write_csv(data, 'test.csv')

data_continent = data %>%
  group_by(iso3, continent, interaction, probability, climate_scenario) %>%
  summarize(
    # mean_depth = mean(mean_depth, na.rm = TRUE),
    flooded_area_km2 = mean(flooded_area_km2, na.rm = TRUE),
  )

data_continent = data_continent %>%
  group_by(interaction, continent, probability, climate_scenario) %>%
  summarize(
    # mean_depth = mean(mean_depth, na.rm = TRUE),
    flooded_area_km2 = sum(flooded_area_km2, na.rm = TRUE)
  )

df_errorbar <-
  data_continent |>
  group_by(continent, interaction, probability) |>
  summarize(
    flooded_area_km2 = sum(flooded_area_km2),
  ) #|>
  # group_by(interaction, probability) |>
  # summarize(
  #   continent = 'Africa',
  #   flooded_area_km2 = sum(flooded_area_km2),
  # )

max_y_value = max(data_continent$flooded_area_km2, na.rm=TRUE)

plot3 = 
  ggplot(data_continent, 
         aes(x=continent, y=flooded_area_km2, fill=interaction)) + #, income_group
  # geom_bar(stat="identity", position='stack') +
  geom_bar(stat="identity", position = position_dodge()) +
  # geom_text(data = df_errorbar, 
  #           aes(label = paste(round(flooded_area_km2,2),"m")), size = 1.5,
  #           vjust =-.5, hjust =.5, angle = 0) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=90, hjust=1, vjust=.5, size=7)) +
  labs(colour=NULL,
       # title = "Global Sum of Flooded Riverine Area by Scenario",
       # subtitle = "Reported by Continent, Annual Probability, Year and Climate Scenario.", 
       x = "", y = "Flooded Area\n(Millions km^2)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=7, title='Scenario')) +
  scale_fill_viridis_d(direction=-1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), 
                     limits=c(0, max_y_value+(max_y_value/8))) +
  facet_wrap(~probability, ncol=4, nrow=1)

data_region = data %>%
  group_by(iso3, flood_region, interaction, climate_scenario, probability) %>%
  summarize(
    # mean_depth = mean(mean_depth, na.rm = TRUE),
    flooded_area_km2 = mean(flooded_area_km2, na.rm = TRUE),
  )

data_region = data_region %>%
  group_by(interaction, flood_region, probability, climate_scenario) %>%
  summarize(
    # mean_depth = mean(mean_depth, na.rm = TRUE),
    flooded_area_km2 = sum(flooded_area_km2, na.rm = TRUE)
  )

df_errorbar <-
  data_region |>
  group_by(flood_region, interaction, probability) |>
  summarize(
    flooded_area_km2 = sum(flooded_area_km2),
  ) #|>
  # group_by(interaction, probability) |>
  # summarize(
  #   flood_region = 'Brazil',
  #   flooded_area_km2 = sum(flooded_area_km2),
  # )

max_y_value = max(data_region$flooded_area_km2, na.rm=TRUE)

plot4 = 
  ggplot(data_region, 
         aes(x=flood_region, y=flooded_area_km2, fill=interaction)) + #, income_group
  # geom_bar(stat="identity", position='stack') +
  geom_bar(stat="identity", position = position_dodge()) +
  # geom_text(data = interaction,
  #           aes(label = paste(round(flooded_area_km2,2),"m")), size = 1.5,
  #           vjust =-.5, hjust =.5, angle = 0) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=90, hjust=1, vjust=.5, size=7)) +
  labs(colour=NULL,
       # title = "Global Sum of Flooded Riverine Area by Scenario",
       # subtitle = "Reported by Flood Region, Annual Probability, Year and Climate Scenario.", 
       x = "", y = "Flooded Area\n(Millions km^2)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=7, title='Flood\nRegion')) +
  scale_fill_viridis_d(direction=-1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), 
                     limits=c(0, max_y_value+(max_y_value/8))) +
  facet_wrap(~probability, ncol=4, nrow=1)


ggarrange(
  plot1, 
  # plot2, 
  plot3, 
  # plot4, 
  labels = c("A", "B", "C", "D"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 2)

path = file.path(folder, 'figures', 'hazard_layer_stats_continent_dodged.png')
ggsave(path, units="in", width=8, height=6, dpi=600)

# ggarrange(
#   # plot1, 
#   plot2,
#   # plot3, 
#   plot4,
#   labels = c("A", "B", "C", "D"),
#   common.legend = TRUE,
#   legend = 'bottom',
#   ncol = 1, nrow = 2)
# 
# path = file.path(folder, 'figures', 'hazard_layer_stats_flood-region_dodged.png')
# ggsave(path, units="in", width=8, height=7, dpi=600)
