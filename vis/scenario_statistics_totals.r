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
    flooded_area_km2 = mean(flooded_area_km2),
    # high = sum(high)
  ) |>
  group_by(interaction, probability) |>
  summarize(
    continent = 'Africa',
    # low = sum(low),
    flooded_area_km2 = mean(flooded_area_km2),
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
  # theme(legend.position = '',
  #       axis.text.x = element_text(angle=90, hjust=1, vjust=.5, size=7)) +
  theme(legend.position = 'bottom',
        text = element_text(family = "Arial", size = 6),
        axis.title = element_text(size = 7),
        axis.text = element_text(size = 6),
        strip.text = element_text(size = 6),
        legend.title = element_text(size = 7),
        legend.text = element_text(size = 6),
        axis.text.x = element_text(angle=90, hjust=1, vjust=.5, size=6)
  ) +
  labs(colour=NULL,
       # title = "Global Sum of Flood Coastal Area by Scenario",
       # subtitle = "Reported by Continent, Annual Probability, Year and Climate Scenario.", 
       x = "", y = "Flood Area\n(Millions of km^2)", fill=NULL) +
  theme(legend.position = 'bottom', panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=7, title='Scenario')
  ) +
  scale_fill_viridis_d(direction=-1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), limits=c(0, max_y_value+.02), labels = scales::comma) +
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

test = data %>%
  group_by(iso3, continent, interaction, return_period) %>%
  summarize(
    # mean_depth = mean(mean_depth, na.rm = TRUE),
    flooded_area_km2 = mean(flooded_area_km2, na.rm = TRUE),
  ) 
test2 = test %>%
  group_by(continent, interaction, return_period) %>%
  summarize(
    # mean_depth = mean(mean_depth, na.rm = TRUE),
    flooded_area_km2 = sum(flooded_area_km2, na.rm = TRUE),
  ) 
write_csv(test, file.path(folder, 'test.csv'))

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
    flooded_area_km2 = mean(flooded_area_km2),
  ) #|>
  # group_by(interaction, probability) |>
  # summarize(
  #   continent = 'Africa',
  #   flooded_area_km2 = sum(flooded_area_km2),
  # )

max_y_value = max(data_continent$flooded_area_km2, na.rm=TRUE)

plot2 = 
  ggplot(data_continent, 
         aes(x=continent, y=flooded_area_km2, fill=interaction)) + #, income_group
  # geom_bar(stat="identity", position='stack') +
  geom_bar(stat="identity", position = position_dodge()) +
  # geom_text(data = df_errorbar, 
  #           aes(label = paste(round(flooded_area_km2,2),"m")), size = 1.5,
  #           vjust =-.5, hjust =.5, angle = 0) +
  theme(legend.position = 'bottom',
        text = element_text(family = "Arial", size = 6),
        axis.title = element_text(size = 7),
        axis.text = element_text(size = 6),
        strip.text = element_text(size = 6),
        legend.title = element_text(size = 7),
        legend.text = element_text(size = 6),
        axis.text.x = element_text(angle=90, hjust=1, vjust=.5, size=6)
  ) +
  labs(colour=NULL,
       # title = "Global Sum of Flooded Riverine Area by Scenario",
       # subtitle = "Reported by Continent, Annual Probability, Year and Climate Scenario.", 
       x = "", y = "Flood Area\n(Millions of km^2)", fill=NULL) +
  theme(panel.spacing = unit(0.6, "lines")) + 
  expand_limits(y=0) +
  guides(fill=guide_legend(ncol=7, title='Scenario')) +
  scale_fill_viridis_d(direction=-1) +
  scale_x_discrete(expand = c(0, 0.15)) +
  scale_y_continuous(expand = c(0, 0), 
                     limits=c(0, max_y_value), labels = scales::comma) +
  facet_wrap(~probability, ncol=4, nrow=1)



ggarrange(
  plot1, 
  plot2,
  # plot3, 
  # plot4, 
  labels = c("A", "B"),
  font.label = list(
    size = 7,
    face = "bold",
    family = "Arial"
  ),
  common.legend = TRUE,
  legend = 'bottom',
  ncol = 1, nrow = 2)

path = file.path(folder, 'figures_new', 'hazard_layer_stats_continent_dodged.png')
ggsave(path, units="in", width=8, height=6, dpi=900)

### Export final Nat Comms figure
fig_dir <- file.path(folder, "figures_final_nat_comms")
if (!dir.exists(fig_dir)) {
  dir.create(fig_dir, recursive = TRUE)
}
path <- file.path(fig_dir, "hazard_layer_stats_continent_dodged.pdf")
ggsave(
  filename = path,
  device = cairo_pdf,
  units = "mm",
  width = 180,
  height = 135
)
