## Visualization script for climate scenarios
library(tidyverse)
library(ggpubr)

###################
##### Coastal flooding
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, '..', 'validation')
setwd(data_directory)

data = read_csv('scenario_stats.csv')

data$mean_depth = gsub("-", 'NA', data$mean_depth)
# data$max_depth = gsub("-", 'NA', data$max_depth)
# data$flooded_area_km2 = gsub("-", 'NA', data$flooded_area_km2)

data$mean_depth = as.numeric(as.character(data$mean_depth))
# data$max_depth = as.numeric(as.character(data$max_depth))
# data$flooded_area_km2 = as.numeric(as.character(data$flooded_area_km2))

data = data[data$hazard == 'inuncoast',]
# data = data[data$iso3 == 'USA',]

country_info = read_csv(file.path(folder, '..', 'data','raw', 'countries.csv'))
country_info = select(country_info, iso3, continent)
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
                            "Historical 1980",
                            "Historical 2030",
                            "Historical 2050",
                            "Historical 2080",
                            "RCP4.5 2030",
                            "RCP8.5 2030",
                            "RCP4.5 2050",
                            "RCP8.5 2050",
                            "RCP4.5 2080",
                            "RCP8.5 2080"),
)

data_aggregated = data %>%
  group_by(interaction, continent, probability, climate_scenario) %>%
  summarize(
    mean_value = mean(mean_depth, na.rm = TRUE)
  )

# write_csv(test, 'global_scenario_stats.csv')

# max_values = data_aggregated %>%
#   group_by(interaction, probability, climate_scenario) %>%
#   summarize(
#     mean_value = sum(mean_value, na.rm = TRUE)
#   )
df_errorbar <-
  data_aggregated |>
  group_by(continent, interaction, probability) |>
  summarize(
    # low = sum(low),
    mean_value = sum(mean_value),
    # high = sum(high)
  ) |>
  group_by(interaction, probability) |>
  summarize(
    continent = 'Africa',
    # low = sum(low),
    mean_value = sum(mean_value),
    # high = sum(high)
  )
max_y_value = max(df_errorbar$mean_value, na.rm=TRUE)

plot1 = 
  ggplot(data_aggregated, 
         aes(x=interaction, y=mean_value, fill=continent)) + #, income_group
  geom_bar(stat="identity", position='stack') +
  geom_text(data = df_errorbar, aes(label = paste(round(mean_value,2),"m")), 
            size = 1.2,
            # position = position_dodge(1), 
            vjust =-.5, hjust =.5, angle = 0) +
  theme(legend.position = '',
        axis.text.x = element_text(angle=60, hjust=1)) +
  labs(colour=NULL,
       title = "Global Mean Coastal Flooding Depth by Scenario",
       subtitle = "Reported by Annual Probability, Year and Climate Scenario.", 
       x = "", y = "Mean Inundation Depth (m)", fill=NULL) +
  theme(legend.position = 'bottom', panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=6, title='Continent')
  ) +
  scale_fill_viridis_d(direction=-1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+(max_y_value/4))) +
  facet_wrap(~probability, ncol=4, nrow=1)

###################
##### Riverine flooding
folder = dirname(rstudioapi::getSourceEditorContext()$path)
data_directory = file.path(folder, '..', 'validation')
setwd(data_directory)

data = read_csv('scenario_stats.csv')

data$mean_depth = gsub("-", 'NA', data$mean_depth)
# data$max_depth = gsub("-", 'NA', data$max_depth)
# data$flooded_area_km2 = gsub("-", 'NA', data$flooded_area_km2)

data$mean_depth = as.numeric(as.character(data$mean_depth))
# data$max_depth = as.numeric(as.character(data$max_depth))
# data$flooded_area_km2 = as.numeric(as.character(data$flooded_area_km2))

country_info = read_csv(file.path(folder, '..', 'data','raw', 'countries.csv'))
country_info = select(country_info, iso3, continent)
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
                            # "Historical 2030",
                            # "Historical 2050",
                            # "Historical 2080",
                            "RCP4.5 2030",
                            "RCP8.5 2030",
                            "RCP4.5 2050",
                            "RCP8.5 2050",
                            "RCP4.5 2080",
                            "RCP8.5 2080"),
)

#write_csv(data, 'test.csv')

data_aggregated = data %>%
  group_by(interaction, continent, probability, climate_scenario) %>%
  summarize(
    mean_value = mean(mean_depth, na.rm = TRUE)
  )

# write_csv(test, 'global_scenario_stats.csv')
# max_values = data_aggregated %>%
#   group_by(interaction, probability, climate_scenario) %>%
#   summarize(
#     mean_value = sum(mean_value, na.rm = TRUE)
#   )
df_errorbar <-
  data_aggregated |>
  group_by(continent, interaction, probability) |>
  summarize(
    # low = sum(low),
    mean_value = sum(mean_value),
    # high = sum(high)
  ) |>
  group_by(interaction, probability) |>
  summarize(
    continent = 'Africa',
    # low = sum(low),
    mean_value = sum(mean_value),
    # high = sum(high)
  )

max_y_value = max(df_errorbar$mean_value, na.rm=TRUE)

plot2 = 
  ggplot(data_aggregated, 
       aes(x=interaction, y=mean_value, fill=continent)) + #, income_group
  geom_bar(stat="identity", position='stack') +
  geom_text(data = df_errorbar, 
    aes(label = paste(round(mean_value,2),"m")), size = 1.2,
    vjust =-.5, hjust =.5, angle = 0) +
  theme(legend.position = 'bottom',
        axis.text.x = element_text(angle=60, hjust=1)) +
  labs(colour=NULL,
     title = "Global Mean Riverine Flooding Depth by Scenario",
     subtitle = "Reported by Annual Probability, Year and Climate Scenario.", 
     x = "", y = "Mean Inundation Depth (m)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=6, title='Continent')) +
  scale_fill_viridis_d(direction=-1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), 
                     limits=c(0, max_y_value+(max_y_value/4))) +
  facet_wrap(~probability, ncol=4, nrow=1)

ggarrange(
  plot1, 
  plot2, 
  labels = c("A", "B"),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 2)

path = file.path(folder, 'figures', 'hazard_layer_stats_mean_depth.png')
ggsave(path, units="in", width=8, height=7, dpi=300)


# ###################
# #####Aggregate cells
# folder = dirname(rstudioapi::getSourceEditorContext()$path)
# data_directory = file.path(folder, '..', 'validation')
# setwd(data_directory)
# 
# data = read_csv('scenario_stats.csv')
# 
# # data$mean_depth = gsub("-", 'NA', data$mean_depth)
# # data$max_depth = gsub("-", 'NA', data$max_depth)
# data$flooded_area_km2 = gsub("-", 'NA', data$flooded_area_km2)
# 
# # data$mean_depth = as.numeric(as.character(data$mean_depth))
# # data$max_depth = as.numeric(as.character(data$max_depth))
# data$flooded_area_km2 = as.numeric(as.character(data$flooded_area_km2))
# 
# data = data[data$hazard == 'inuncoast',]
# # data = data[data$iso3 == 'USA',]
# 
# data = data[
#   data$climate_scenario == 'historical' | 
#     data$climate_scenario == 'rcp4p5' | 
#     data$climate_scenario == "rcp8p5",]
# 
# data$climate_scenario = factor(data$climate_scenario,
#                                levels=c("historical","rcp4p5","rcp8p5"),
#                                labels=c("Historical","RCP4.5","RCP8.5")
# )
# 
# data$return_period = factor(data$return_period,
#                             levels=c(
#                               "rp0100",
#                               "rp0250",
#                               "rp0500",
#                               "rp1000"
#                             ),
#                             labels=c(
#                               "1-in-100-Years",
#                               "1-in-250-Years",
#                               "1-in-500-Years",
#                               "1-in-1000-Years"
#                             )
# )
# 
# #convert to probability_of_exceedance 
# data$probability = ''
# data$probability[data$return_period == "1-in-100-Years"] = "1%" # (1/100) * 100 = 1%
# data$probability[data$return_period == "1-in-250-Years"] = "0.4%" # (1/250) * 100 = .4%
# data$probability[data$return_period == "1-in-500-Years"] = "0.2%" # (1/500) * 100 = .2%
# data$probability[data$return_period == "1-in-1000-Years"] = "0.1%" # (1/1000) * 100 = .1%
# 
# 
# data$probability = factor(data$probability,
#                           levels=c(
#                             "0.1%",
#                             "0.2%",
#                             "0.4%",
#                             "1%"
#                           )
# )
# 
# data$interaction = paste(data$climate_scenario, data$year)
# 
# data$interaction = factor(data$interaction,
#                           levels=c(
#                             "Historical hist",
#                             "Historical 2030",
#                             "Historical 2050",
#                             "Historical 2080",
#                             "RCP4.5 2030",
#                             "RCP8.5 2030",
#                             "RCP4.5 2050",
#                             "RCP8.5 2050",
#                             "RCP4.5 2080",
#                             "RCP8.5 2080"),
#                           labels = c(
#                             "Historical 1980",
#                             "Historical 2030",
#                             "Historical 2050",
#                             "Historical 2080",
#                             "RCP4.5 2030",
#                             "RCP8.5 2030",
#                             "RCP4.5 2050",
#                             "RCP8.5 2050",
#                             "RCP4.5 2080",
#                             "RCP8.5 2080"),
# )
# 
# data_aggregated = data %>%
#   group_by(interaction, probability, climate_scenario) %>%
#   summarize(
#     value = sum(flooded_area_km2, na.rm = TRUE) / 1e6
#   )
# 
# # write_csv(test, 'global_scenario_stats.csv')
# 
# max_y_value = max(data_aggregated$value, na.rm=TRUE)
# 
# plot1 = 
#   ggplot(data_aggregated, 
#          aes(x=interaction, y=value, fill=interaction)) + #, income_group
#   geom_bar(stat="identity", position='stack') +
#   # geom_errorbar(data=df_errorbar, aes(y=mean, ymin=low, ymax=high),
#   #               position = position_dodge(1),
#   #               lwd = 0.2,
#   #               show.legend = FALSE, width=0.4,  color="#FF0000FF") +
#   geom_text(data = data_aggregated, aes(label = paste(round(value,2),"m")), size = 1.8,
#             position = position_dodge(1), vjust =-.5, hjust =.5, angle = 0) +
#   theme(legend.position = '',
#         axis.text.x = element_text(angle=45, hjust=1)) +
#   labs(colour=NULL,
#        title = "Global Coastal Area Vulnerable to Flooding by Scenario",
#        subtitle = "Reported by Annual Probability, Year and Climate Scenario.", 
#        x = "", y = "Million Area (km^2)", fill=NULL) +
#   theme(panel.spacing = unit(0.6, "lines")) + 
#   expand_limits(y=0) +
#   guides(fill=NULL #guide_legend(ncol=3, title='Income Group')
#   ) +
#   scale_fill_viridis_d(direction=-1) +
#   scale_x_discrete(expand = c(0, 0.15)) +
#   scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+(max_y_value/4))) +
#   facet_wrap(~probability, ncol=4, nrow=1)
# 
# ###################
# #####Aggregate cells
# folder = dirname(rstudioapi::getSourceEditorContext()$path)
# data_directory = file.path(folder, '..', 'validation')
# setwd(data_directory)
# 
# data = read_csv('scenario_stats.csv')
# 
# # data$mean_depth = gsub("-", 'NA', data$mean_depth)
# # data$max_depth = gsub("-", 'NA', data$max_depth)
# data$flooded_area_km2 = gsub("-", 'NA', data$flooded_area_km2)
# 
# # data$mean_depth = as.numeric(as.character(data$mean_depth))
# # data$max_depth = as.numeric(as.character(data$max_depth))
# data$flooded_area_km2 = as.numeric(as.character(data$flooded_area_km2))
# 
# data = data[data$hazard == 'inunriver',]
# # data = data[data$iso3 == 'USA',]
# 
# data = data[
#   data$climate_scenario == 'historical' | 
#     data$climate_scenario == 'rcp4p5' | 
#     data$climate_scenario == "rcp8p5",]
# 
# data$climate_scenario = factor(data$climate_scenario,
#                                levels=c("historical","rcp4p5","rcp8p5"),
#                                labels=c("Historical","RCP4.5","RCP8.5")
# )
# 
# data$return_period = factor(data$return_period,
#                             levels=c(
#                               "rp00100",
#                               "rp00250",
#                               "rp00500",
#                               "rp01000"
#                             ),
#                             labels=c(
#                               "1-in-100-Years",
#                               "1-in-250-Years",
#                               "1-in-500-Years",
#                               "1-in-1000-Years"
#                             )
# )
# 
# #convert to probability_of_exceedance 
# data$probability = ''
# data$probability[data$return_period == "1-in-100-Years"] = "1%" # (1/100) * 100 = 1%
# data$probability[data$return_period == "1-in-250-Years"] = "0.4%" # (1/250) * 100 = .4%
# data$probability[data$return_period == "1-in-500-Years"] = "0.2%" # (1/500) * 100 = .2%
# data$probability[data$return_period == "1-in-1000-Years"] = "0.1%" # (1/1000) * 100 = .1%
# 
# data$probability = factor(data$probability,
#                           levels=c(
#                             "0.1%",
#                             "0.2%",
#                             "0.4%",
#                             "1%"
#                           )
# )
# 
# data$interaction = paste(data$climate_scenario, data$year)
# 
# data$interaction = factor(data$interaction,
#                           levels=c(
#                             "Historical 1980",
#                             # "Historical 2030",
#                             # "Historical 2050",
#                             # "Historical 2080",
#                             "RCP4.5 2030",
#                             "RCP8.5 2030",
#                             "RCP4.5 2050",
#                             "RCP8.5 2050",
#                             "RCP4.5 2080",
#                             "RCP8.5 2080"),
# )
# 
# data_aggregated = data %>%
#   group_by(interaction, probability, climate_scenario) %>%
#   summarize(
#     value = sum(flooded_area_km2, na.rm = TRUE) / 1e6
#   )
# 
# # write_csv(test, 'global_scenario_stats.csv')
# 
# max_y_value = max(data_aggregated$value, na.rm=TRUE)
# 
# plot2 = 
#   ggplot(data_aggregated, 
#          aes(x=interaction, y=value, fill=interaction)) + #, income_group
#   geom_bar(stat="identity", position='stack') +
#   # geom_errorbar(data=df_errorbar, aes(y=mean, ymin=low, ymax=high),
#   #               position = position_dodge(1),
#   #               lwd = 0.2,
#   #               show.legend = FALSE, width=0.4,  color="#FF0000FF") +
#   geom_text(data = data_aggregated, aes(label = paste(round(value,2),"m")), size = 1.8,
#             position = position_dodge(1), vjust =-.5, hjust =.5, angle = 0) +
#   theme(legend.position = '',
#         axis.text.x = element_text(angle=45, hjust=1)) +
#   labs(colour=NULL,
#        title = "Global Riverine Area Vulnerable to Flooding by Scenario",
#        subtitle = "Reported by Annual Probability, Year and Climate Scenario.", 
#        x = "", y = "Area (Million km^2)", fill=NULL) +
#   theme(panel.spacing = unit(0.6, "lines")) + 
#   expand_limits(y=0) +
#   guides(fill=NULL #guide_legend(ncol=3, title='Income Group')
#   ) +
#   scale_fill_viridis_d(direction=-1) +
#   scale_x_discrete(expand = c(0, 0.15)) +
#   scale_y_continuous(expand = c(0, 0), 
#                      limits=c(0, max_y_value+(max_y_value/4))) +
#   facet_wrap(~probability, ncol=4, nrow=1)
# 
# ggarrange(
#   plot1, 
#   plot2, 
#   labels = c("A", "B"),
#   # common.legend = NULL,
#   legend = 'none',
#   ncol = 1, nrow = 2)
# 
# path = file.path(folder, 'figures', 'hazard_layer_stats_mean_area.png')
# ggsave(path, units="in", width=8, height=7, dpi=300)
# 
# 
# 
# 
# 
